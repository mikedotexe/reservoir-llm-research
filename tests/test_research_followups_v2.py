import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


v2 = module("followups_v2_test_target", ROOT / "probes/research_followups_v2.py")
fixtures = module("followups_v1_fixtures", ROOT / "tests/test_research_followups.py")


class ProviderAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.FollowupTests(); self.f.setUp()
        self.p = self.f.p; self.start = self.f.start + 600
        self.pre = dict(schema="provider_observer_preflight_v1", completed_at=v2.iso(self.start-120),
            outcomes_read=0, raw_responses_read=0, service_operations=0, live_source_writes=0,
            coverage_status="unavailable_within_frozen_scope", exhaustive_denominator_verified=False)
        self.a = dict(schema="bounded_followups_provider_amendment_v1", frozen_at=v2.iso(self.start-60),
            provider_t0=v2.iso(self.start), provider_end=v2.iso(self.start+86400),
            provider_collection_allowance_seconds=120, original_cohort_t0=self.p["t0"],
            original_intake_end=self.p["intake_end"], original_final_end=self.p["final_end"],
            coverage_status=self.pre["coverage_status"], exhaustive_denominator_verified=False)

    def tearDown(self): self.f.tearDown()

    def test_separate_provider_clock_preserves_original_cohorts(self):
        before = copy.deepcopy(self.p)
        v2.validate_amendment(self.a, self.p, self.pre)
        pp = v2.provider_protocol(self.p, self.a)
        self.assertEqual(self.p, before)
        self.assertEqual(pp["t0"], self.a["provider_t0"])
        self.assertEqual(pp["provider_end"], self.a["provider_end"])
        self.assertEqual(pp["allowlist"], self.p["allowlist"])

    def test_reject_window_before_preflight_or_not_exactly_24h(self):
        for field, value in [("frozen_at", v2.iso(self.start-121)),
                             ("provider_end", v2.iso(self.start+86401)),
                             ("provider_t0", v2.iso(self.start-121))]:
            a = copy.deepcopy(self.a); a[field] = value
            with self.assertRaises((AssertionError, ValueError)): v2.validate_amendment(a, self.p, self.pre)

    def test_reject_preflight_outcomes_services_or_coverage_promotion(self):
        for key in ["outcomes_read", "raw_responses_read", "service_operations", "live_source_writes"]:
            pre = dict(self.pre); pre[key] = 1
            with self.assertRaises(AssertionError): v2.validate_amendment(self.a, self.p, pre)
        for key, value in [("exhaustive_denominator_verified", True), ("coverage_status", "verified")]:
            a = dict(self.a); a[key] = value
            with self.assertRaises(AssertionError): v2.validate_amendment(a, self.p, self.pre)

    def test_reject_changed_cohort_deadlines(self):
        for key in ["original_cohort_t0", "original_intake_end", "original_final_end"]:
            a = dict(self.a); a[key] = v2.iso(self.start)
            with self.assertRaises(AssertionError): v2.validate_amendment(a, self.p, self.pre)

    def test_no_provider_reads_between_original_and_amended_start(self):
        pp = v2.provider_protocol(self.p, self.a)
        reader = fixtures.Reader()
        result = v2.capture_provider(pp, self.start-1, reader)
        self.assertEqual(result["status"], "awaiting_window")
        self.assertEqual(reader.inventories, [])

    def test_provider_selection_excludes_superseded_window(self):
        self.f.provider(1); selected, _ = self.f.provider(601)
        pp = v2.provider_protocol(self.p, self.a)
        cap = v2.capture_provider(pp, self.start+20)
        summary = v2.analyze_provider(pp, [cap], self.start+20)
        self.assertEqual(summary["dispatches"], 1)
        records = [r for r in cap["records"] if r["kind"] == "provider_dispatch"]
        self.assertEqual(len(records), 1)
        self.assertIn(selected, records[0]["path"])

    def test_amended_status_retains_unavailable_preflight(self):
        pp = v2.provider_protocol(self.p, self.a)
        cap = dict(runs=v2.capture_runs(self.p, self.start-1), provider=v2.capture_provider(pp, self.start-1))
        result = v2.summary(self.p, pp, [cap], self.start-1, [], self.a)
        self.assertEqual(result["s006_provider"]["preflight_coverage_status"], "unavailable_within_frozen_scope")
        self.assertFalse(result["s006_provider"]["exhaustive_denominator_verified"])


if __name__ == "__main__": unittest.main()
