import importlib.util
from pathlib import Path
import unittest
import json
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("run_analysis", Path(__file__).with_name("analyze_run.py"))
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class WorkflowChecks(unittest.TestCase):
    def rows(self):
        result = []
        for i in range(4):
            row = {"elapsedSeconds": i * 15, "wallEpochNs": str((100 + i * 15) * 10**9), "sampleSeconds": .5,
                   "process": {"rssBytes": 100 + i, "cpuIntervalPercent": None if i == 0 else i * 10},
                   "disk": {"complete": True, "logicalBytes": i * 100, "allocatedBytes": i * 4096},
                   "manifest": {"phase": "running", "durableStep": i * 15}}
            if result:
                row["_previousCpu"] = result[-1]
            result.append(row)
        return result

    def test_load_crossing_cpu_is_excluded_but_later_point_read_remains(self):
        result = workflow.summarize(self.rows(), 0, 45, [(105, 110)])
        cpu = result["metrics"]["cpuIntervalPercent"]
        self.assertEqual(cpu["excludedByDocumentedLoadCount"], 1)
        self.assertEqual(cpu["statistics"]["count"], 2)
        self.assertEqual(cpu["durationWeightedMeanPercent"], 25)
        self.assertEqual(result["metrics"]["rssBytes"]["statistics"]["count"], 4)
        self.assertEqual(result["manifestProgressUnfiltered"]["last"][1]["durableStep"], 45)

    def test_disk_scan_interval_overlap_is_excluded(self):
        result = workflow.summarize(self.rows(), 0, 45, [(115.25, 115.30)])
        self.assertEqual(result["metrics"]["logicalBytes"]["excludedByDocumentedLoadCount"], 1)
        self.assertEqual(result["metrics"]["rssBytes"]["excludedByDocumentedLoadCount"], 0)

    def test_window_cpu_bounds_and_incomplete_disk_not_zero(self):
        rows = self.rows()
        rows[2]["disk"]["complete"] = False
        result = workflow.summarize(rows, 10, 30, [])
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["statistics"]["count"], 1)
        self.assertEqual(result["metrics"]["logicalBytes"]["statistics"]["count"], 1)
        self.assertEqual(result["metrics"]["logicalBytes"]["statistics"]["first"], 100)

    def test_weighted_cpu_mean_uses_actual_interval_lengths(self):
        rows = self.rows()
        rows[3]["elapsedSeconds"] = 60
        rows[3]["wallEpochNs"] = str(160 * 10**9)
        result = workflow.summarize(rows, 0, 60, [])
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["coveredCpuIntervalSeconds"], 60)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["durationWeightedMeanPercent"], 22.5)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["statistics"]["median"], 20)

    def test_main_preserves_errors_missing_cpu_gap_and_incomplete_windows(self):
        with tempfile.TemporaryDirectory(prefix="analysis-workflow-fixture-") as directory:
            root = Path(directory)
            capture, markers, output = root / "samples.jsonl", root / "markers.jsonl", root / "report.json"
            header = {"type": "header", "schema": workflow.sampler.SCHEMA, "intervalSeconds": 15, "monotonicNs": "1000000000", "process": {"pid": 999}}
            samples = []
            for i, source in enumerate(self.rows()):
                row = {k: v for k, v in source.items() if k != "_previousCpu"}
                row.update({"type": "sample", "sequence": i, "monotonicNs": str((1 + 15 * i) * 10**9), "errors": []})
                row["process"]["cpuTotalNanoseconds"] = str(i * 1000)
                samples.append(row)
            samples[1]["process"] = None
            samples[1]["errors"] = [{"component": "process", "kind": "OSError", "message": "Synthetic unavailable task read"}]
            footer = {"type": "footer", "sampleCount": 4, "status": "completed"}
            capture.write_text("".join(json.dumps(row) + "\n" for row in [header, *samples, footer]))
            markers.write_text(json.dumps({"phase": "visible", "monotonicNs": "1000000000"}) + "\n" + json.dumps({"phase": "minimized", "monotonicNs": "11000000000"}) + "\n")
            with patch.object(workflow.sys, "argv", ["analyze_run.py", "--input", str(capture), "--markers", str(markers), "--output", str(output)]):
                workflow.main()
            report = json.loads(output.read_text())
            self.assertEqual(report["base"]["coverage"]["sampleErrorCount"], 1)
            minimized = next(w for w in report["windows"] if w["id"].endswith("minimized"))
            # Missing sample15 means CPU at30 spans0..30 and crosses minimize10;
            # only30..45 belongs entirely to the phase. No nominal15s substitute.
            cpu = minimized["allObservedResources"]["metrics"]["cpuIntervalPercent"]
            self.assertEqual(cpu["statistics"]["count"], 1)
            self.assertEqual(cpu["statistics"]["first"], 30)
            self.assertEqual(cpu["coveredCpuIntervalSeconds"], 15)
            for window in report["windows"]:
                if window["id"].startswith("prospective-"):
                    self.assertTrue(window["qualificationNote"].startswith("INCOMPLETE"))
            self.assertEqual(minimized["documentedLoadExcludedResources"]["manifestProgressUnfiltered"]["last"][1]["durableStep"], 45)


if __name__ == "__main__":
    unittest.main()
