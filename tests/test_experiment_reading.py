"""Fixed reading selection, missingness, and exact evidence boundaries."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from reservoir_experiments import reading, runner
from reservoir_experiments.transport import json_bytes
from tests.test_experiment_runner import FixtureTransport, node, protocol, response


def sample_node(nid, *, episode="case-0", condition="arm-secret", kind="target", seed=7, index=0, delay="delayed"):
    value = node(nid, kind=kind, content="Supplied evidence only.")
    value.update(episode=episode, condition=condition, seed=seed,
                 metadata={"case_index": index, "delay": delay})
    return value


class SelectionTests(unittest.TestCase):
    def test_attribution_and_catalog_fixed_history_seed_and_repeat_selection(self):
        for study, kind in (("S-013", "prose"), ("S-016", "catalog")):
            nodes = []
            for index in range(24):
                for seed in (7, 20260909):
                    nodes.append(sample_node(f"n-{index}-{seed}", kind=kind, seed=seed, index=index,
                                             episode=f"history-{index}"))
            repeated = deepcopy(nodes[0])
            repeated["id"] = "repeat"
            repeated["metadata"]["replicate"] = True
            nodes.append(repeated)
            nodes.append(sample_node("different-kind", kind="attribution"))
            p = protocol(*nodes)
            p["study"] = study
            selected = reading._selected_opportunities(p)
            self.assertEqual(len(selected), 8)
            self.assertEqual({s["episode"] for s in selected},
                             {f"history-{index}" for index in reading.PRESELECTED_CASE_INDICES})
            self.assertTrue(all(s["seed"] == 7 for s in selected))
            self.assertEqual(selected, reading._selected_opportunities(p))
            # Availability cannot change selection; input order does not reveal pairing.
            p["nodes"].reverse()
            self.assertEqual(selected, reading._selected_opportunities(p))

    def test_correction_selects_twelve_variant_zero_targets(self):
        cases = [{"id": f"case-{v}-{i}", "variant": v} for v in range(4) for i in range(12)]
        nodes = [sample_node(f"{c['id']}-target-s{seed}", episode=c["id"], seed=seed)
                 for c in cases for seed in (7, 20260909)]
        nodes.append(sample_node("forecast", kind="forecast"))
        p = protocol(*nodes)
        p.update(study="S-014", cases=cases)
        selected = reading._selected_opportunities(p)
        self.assertEqual(len(selected), 12)
        self.assertEqual({s["episode"] for s in selected}, {f"case-0-{i}" for i in range(12)})

    def test_memory_retains_all_sixty_slots_when_sources_are_unavailable(self):
        cases = [{"id": f"case-{i}", "variant": 0} for i in range(12)]
        cases += [{"id": "nonselected", "variant": 1}]
        nodes = [sample_node(f"n-{i}-{arm}-{seed}-{delay}", episode=f"case-{i}", condition=arm,
                             kind="application", seed=seed, delay=delay)
                 for i in range(10) for arm in reading.MEMORY_ARMS
                 for seed in (7, 20260909) for delay in ("delayed", "immediate")]
        p = protocol(*nodes)
        p.update(study="S-015", split="replication", cases=cases,
                 unavailable_sources=[{"episode": "case-10"}, {"episode": "case-11"}])
        selected = reading._selected_opportunities(p)
        self.assertEqual(len(selected), 60)
        self.assertEqual(sum(s["node_id"] is None for s in selected), 10)
        self.assertEqual(sum(s["source_unavailable"] for s in selected), 10)
        self.assertEqual({s["condition"] for s in selected}, set(reading.MEMORY_ARMS))

    def test_replication_intersects_preselected_catalog_cases(self):
        p = protocol(*(sample_node(f"n-{i}", episode=f"history-{i}", kind="catalog", index=i)
                       for i in (0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19)))
        p.update(study="S-016", split="replication")
        self.assertEqual(len(reading._selected_opportunities(p)), 4)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.run = self.root / "research/outputs/run"
        self.output = self.root / "research/outputs/readers"

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, p):
        path = self.root / "protocol.json"
        path.write_bytes(json_bytes(p))
        runner.prepare(path, self.run, repository=self.root)

    def test_export_exact_rendered_messages_without_allocation_truth_or_metadata(self):
        parent = sample_node("node-parent-secret", kind="initial")
        target = sample_node("node-target-secret", kind="target")
        target["inputs"] = [parent["id"]]
        target["messages"][1]["content"] = "Exact earlier output:\n{{output:node-parent-secret}}\nTrailing spaces  "
        p = protocol(parent, target)
        p.update(study="S-014", cases=[{"id": "case-0", "variant": 0}])
        self.prepare(p)
        text = "Model prose.\n```\n## Packet 999\n```\n"
        runner.run_protocol(self.run, transport=FixtureTransport([response("Observed parent."), response(text)]))
        receipt = reading.study_reading(self.run, self.output)
        output = (self.output / "reading.md").read_text()
        evidence = (self.output / "evidence.md").read_text()
        self.assertIn(text, output)
        self.assertIn("Exact earlier output:\nObserved parent.\nTrailing spaces  ", evidence)
        self.assertNotIn("Observed parent.", output)
        for secret in ("node-parent-secret", "node-target-secret", "arm-secret", "EVALUATOR_ONLY_SECRET", "fixture:1", "test-protocol"):
            self.assertNotIn(secret, output)
            self.assertNotIn(secret, evidence)
        self.assertIn("````text", output)
        self.assertEqual(receipt["complete"], 1)
        key = runner.read_json(self.output / "allocation-key.json")
        self.assertEqual(key[0]["node_id"], target["id"])
        self.assertEqual(key[0]["message_count"], 2)
        for filename, digest in receipt["files"].items():
            self.assertEqual(runner.sha((self.output / filename).read_bytes()), digest)

    def test_missing_and_incomplete_slots_are_retained_without_substitution(self):
        nodes = [sample_node(f"n-{i}", episode=f"case-{i}") for i in range(3)]
        p = protocol(*nodes)
        p.update(study="S-014", cases=[{"id": f"case-{i}", "variant": 0} for i in range(3)])
        self.prepare(p)
        runner.run_protocol(self.run, limit=2, transport=FixtureTransport([
            response("complete"), response("partial", done_reason="length")]))
        receipt = reading.study_reading(self.run, self.output)
        self.assertEqual(receipt["selected"], 3)
        self.assertEqual(receipt["complete"], 1)
        self.assertEqual(receipt["incomplete"], 1)
        self.assertEqual(receipt["status_counts"], {"complete": 1, "incomplete": 1, "pending": 1})
        self.assertEqual(len(receipt["missing_selected_opportunities"]), 2)
        document = (self.output / "reading.md").read_text()
        self.assertEqual(document.count("\n## Packet "), 3)
        self.assertIn("partial", document)
        self.assertIn("Status: pending.", document)
        self.assertIn("No rendered request", (self.output / "evidence.md").read_text())

    def test_source_unavailable_has_opaque_slots_and_no_guessed_request(self):
        p = protocol(sample_node("available", episode="case-0", condition="original", kind="application"))
        p.update(study="S-015", cases=[{"id": "case-0", "variant": 0}, {"id": "case-1", "variant": 0}],
                 unavailable_sources=[{"episode": "case-1"}])
        self.prepare(p)
        receipt = reading.study_reading(self.run, self.output)
        self.assertEqual(receipt["planned"], 10)
        self.assertEqual(receipt["source_unavailable"], 5)
        self.assertEqual(receipt["status_counts"]["not_scheduled"], 4)
        self.assertEqual((self.output / "reading.md").read_text().count("\n## Packet "), 10)
        self.assertEqual((self.output / "evidence.md").read_text().count("No rendered request"), 10)

    def test_export_refuses_tampered_run_and_existing_or_external_destination(self):
        p = protocol(sample_node("target"))
        p.update(study="S-014", cases=[{"id": "case-0", "variant": 0}])
        self.prepare(p)
        reading.study_reading(self.run, self.output)
        with self.assertRaisesRegex(runner.ExperimentError, "existing"):
            reading.study_reading(self.run, self.output)
        with self.assertRaisesRegex(runner.ExperimentError, "inside"):
            reading.study_reading(self.run, self.root.parent / "reader-outside")
        (self.run / "protocol.json").write_text("{}")
        with self.assertRaisesRegex(runner.ExperimentError, "Snapshot hash"):
            reading.study_reading(self.run, self.root / "research/outputs/tampered")


if __name__ == "__main__":
    unittest.main()
