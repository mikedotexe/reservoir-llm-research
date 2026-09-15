"""Numerical and provenance contracts for a research-only full-vector planner."""
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

PATH = Path(__file__).resolve().parents[1] / "probes/substrate_pattern_plan.py"
SPEC = importlib.util.spec_from_file_location("substrate_pattern_plan", PATH)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class PatternPlanTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"target": "synthetic.native_esn", "dimensions": 4,
                         "capture_column_order_id": "synthetic:columns-v1",
                         "node_layout_id": None, "model_sha256": None}
        self.reference = np.array([0.1, -0.1, 0.1, 0.0])
        patterns = {f"mode{i}": {"vector": np.eye(4)[i].tolist(),
                                "provenance": {"source": "synthetic exact basis", "index": i}}
                    for i in range(4)}
        self.registry = probe.make_registry(self.identity, self.reference, patterns, {"kind": "synthetic"})
        self.state = np.array([0.5, 0.2, -0.3, 0.6])
        self.limits = {"max_step_l2": 2, "max_coordinate_delta": 2, "max_total_requested_l2": 4}

    def evidence(self, state=None):
        state = self.state if state is None else state
        return {"identity": copy.deepcopy(self.identity), "vector": list(state),
                "vector_sha256": probe.vector_hash(state), "source": "synthetic"}

    def plan(self, operation, **kwargs):
        return probe.make_plan(self.registry, self.evidence(kwargs.pop("state", None)),
                               {"steps": [{"success_step_offset": 0, "operation": operation, **kwargs}]}, self.limits)

    def test_signed_combination_normalizes_direction_once(self):
        operation = {"kind": "combine", "terms": {"mode0": 3, "mode1": -4}, "amount": -0.25}
        item = self.plan(operation)["steps"][0]
        np.testing.assert_allclose(item["requested_delta"], [-0.15, 0.2, 0, 0], rtol=0, atol=1e-16)
        self.assertAlmostEqual(item["requested_l2"], 0.25)
        np.testing.assert_allclose(item["headroom_preview"]["preview_state"], [0.35, 0.4, -0.3, 0.6])

    def test_suppress_changes_only_named_reference_centered_component(self):
        result = self.plan({"kind": "suppress", "modes": ["mode0", "mode2"], "fraction": 0.5})
        after = result["steps"][0]["headroom_preview"]["preview_state"]
        np.testing.assert_allclose(after, [0.3, 0.2, -0.1, 0.6], rtol=0, atol=1e-15)
        np.testing.assert_array_equal(np.asarray(after)[[1, 3]], self.state[[1, 3]])

    def test_plane_rotation_preserves_radius_and_orthogonal_complement(self):
        result = self.plan({"kind": "rotate", "modes": ["mode0", "mode1"], "angle_radians": math.pi / 2})
        after = np.array(result["steps"][0]["headroom_preview"]["preview_state"])
        np.testing.assert_allclose(after, [-0.2, 0.3, -0.3, 0.6], rtol=0, atol=1e-15)
        self.assertAlmostEqual(np.linalg.norm(after - self.reference), np.linalg.norm(self.state - self.reference))
        np.testing.assert_array_equal(after[2:], self.state[2:])
        reverse, _ = probe.resolve(self.registry, after, self.reference,
                                   {"kind": "rotate", "modes": ["mode0", "mode1"], "angle_radians": -math.pi / 2})
        np.testing.assert_allclose(after + reverse, self.state, atol=1e-15)

    def test_rotation_and_suppression_reject_nonorthogonal_modes(self):
        registry = copy.deepcopy(self.registry)
        registry["patterns"]["mode1"] = copy.deepcopy(registry["patterns"]["mode0"])
        registry = probe.sealed(registry, "registry_sha256")
        for operation in ({"kind": "rotate", "modes": ["mode0", "mode1"], "angle_radians": 0.1},
                          {"kind": "suppress", "modes": ["mode0", "mode1"], "fraction": 0.1}):
            with self.subTest(operation=operation), self.assertRaisesRegex(ValueError, "orthonormal"):
                probe.resolve(registry, self.state, self.reference, operation)

    def test_default_headroom_rejects_and_explicit_attenuation_preserves_direction(self):
        state = np.array([0.95, 0.0, 0.0, 0.0])
        operation = {"kind": "combine", "terms": {"mode0": 1, "mode1": -1}, "amount": 0.4}
        rejected = self.plan(operation, state=state)["steps"][0]
        self.assertEqual(rejected["headroom_preview"]["status"], "rejected_headroom")
        self.assertFalse(rejected["would_dispatch_in_sequence"])
        np.testing.assert_array_equal(rejected["headroom_preview"]["delta"], np.zeros(4))
        accepted = self.plan(operation, state=state, headroom_policy="attenuate")["steps"][0]
        headroom = accepted["headroom_preview"]
        self.assertEqual(headroom["status"], "preview_attenuated")
        np.testing.assert_allclose(headroom["delta"], [0.05, -0.05, 0, 0], rtol=0, atol=1e-15)
        np.testing.assert_allclose(headroom["delta"], headroom["attenuation_factor"] * np.asarray(accepted["requested_delta"]), atol=1e-15)

    def test_zero_headroom_is_unapplied_and_inward_delta_still_fits(self):
        for amount, status in ((0.1, "unapplied_zero_headroom"), (-0.1, "preview_unattenuated")):
            item = self.plan({"kind": "coordinate", "index": 0, "amount": amount},
                             state=np.array([1.0, 0, 0, 0]), headroom_policy="attenuate")["steps"][0]
            self.assertEqual(item["headroom_preview"]["status"], status)

    def test_exact_zero_is_bit_preserving_and_not_successful_application(self):
        self.state[-1] = -0.0
        for operation in ({"kind": "coordinate", "index": 0, "amount": 0.0},
                          {"kind": "suppress", "modes": ["mode0"], "fraction": 0.0},
                          {"kind": "rotate", "modes": ["mode0", "mode1"], "angle_radians": 0.0}):
            item = self.plan(operation)["steps"][0]
            self.assertEqual(item["headroom_preview"]["status"], "exact_noop")
            self.assertFalse(item["would_dispatch_in_sequence"])
            self.assertEqual(np.asarray(item["headroom_preview"]["preview_state"]).tobytes(), self.state.tobytes())
        with self.assertRaisesRegex(ValueError, "zero combination"):
            self.plan({"kind": "combine", "terms": {"mode0": 0}, "amount": 0})

    def test_sub_ulp_request_reports_no_realized_displacement(self):
        item = self.plan({"kind": "coordinate", "index": 0, "amount": 1e-300})["steps"][0]
        self.assertGreater(item["requested_l2"], 0)
        self.assertEqual(item["preview_realized_l2"], 0)
        self.assertEqual(item["headroom_preview"]["status"], "unapplied_rounding")
        self.assertFalse(item["would_dispatch_in_sequence"])

    def test_zero_component_rotation_and_suppression_are_noops(self):
        for operation in ({"kind": "suppress", "modes": ["mode0"], "fraction": 1.0},
                          {"kind": "rotate", "modes": ["mode0", "mode1"], "angle_radians": 1.0}):
            self.assertEqual(self.plan(operation, state=self.reference)["steps"][0]["headroom_preview"]["status"], "exact_noop")

    def test_nan_infinite_and_oversize_reject_without_silent_attenuation(self):
        for amount in (math.nan, math.inf, -math.inf, 1e308, 3.0, True):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.plan({"kind": "coordinate", "index": 0, "amount": amount}, headroom_policy="attenuate")
        for state in ([math.nan, 0, 0, 0], [2, 0, 0, 0], [0, 0]):
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.plan({"kind": "coordinate", "index": 0, "amount": 0}, state=state)
        with self.assertRaises(ValueError):
            probe.make_registry({**self.identity, "dimensions": probe.MAX_DIMENSION + 1}, [], {}, {})

    def test_unknown_identity_previews_but_cannot_be_apply_eligible(self):
        plan = self.plan({"kind": "coordinate", "index": 0, "amount": 0.1})
        self.assertEqual(plan["steps"][0]["headroom_preview"]["status"], "preview_unattenuated")
        self.assertFalse(plan["native_identity_complete"])
        self.assertFalse(plan["apply_eligible"])
        self.assertIn("node_layout_id", plan["unresolved_native_identity"])
        self.assertIn("model_sha256", plan["unresolved_native_identity"])

    def test_layout_model_and_capture_order_mismatches_reject(self):
        for key in ("target", "node_layout_id", "model_sha256", "capture_column_order_id"):
            evidence = self.evidence()
            evidence["identity"][key] = "different"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "compatibility"):
                probe.make_plan(self.registry, evidence, {"steps": []}, self.limits)

    def test_registry_and_state_hashes_reject_tampering(self):
        tampered = copy.deepcopy(self.registry)
        tampered["patterns"]["mode0"]["vector"][0] = -1
        with self.assertRaisesRegex(ValueError, "integrity"):
            probe.validate_registry(tampered)
        tampered = probe.sealed(tampered, "registry_sha256")
        with self.assertRaisesRegex(ValueError, "integrity"):
            probe.validate_registry(tampered)
        evidence = self.evidence()
        evidence["vector"][0] += 0.1
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            probe.make_plan(self.registry, evidence, {"steps": []}, self.limits)

    def test_malformed_registry_maps_fail_as_validation_errors(self):
        for shape in ([], {}, None, "not a map"):
            bad = copy.deepcopy(self.registry)
            bad["patterns"] = shape
            bad = probe.sealed(bad, "registry_sha256")
            with self.subTest(shape=shape), self.assertRaisesRegex(ValueError, "pattern map"):
                probe.validate_registry(bad)

    def test_finite_offsets_cancellation_never_creates_an_inverse(self):
        statuses = probe.cancel_sequence([0, 2, 4], completed=[0], cancel_at=2)
        self.assertEqual([x["status"] for x in statuses], ["hypothetically_completed", "cancelled_pending", "cancelled_pending"])
        self.assertEqual(len(statuses), 3)
        self.assertEqual(probe.cancel_sequence([0], cancel_at=0)[0]["status"], "cancelled_pending")
        self.assertEqual(probe.cancel_sequence([0], completed=[0], cancel_at=1)[0]["status"], "hypothetically_completed")
        for offsets, completed, cancel in (([0, 0], [], None), ([2, 0], [], None),
                                           ([0], [0], 0), ([0, 2], [], 2),
                                           ([0], [1], None), (list(range(65)), [], None),
                                           ([0, 1], [True], None), ([0, 2], [2], None),
                                           ([10001], [], None)):
            with self.subTest(offsets=offsets), self.assertRaises(ValueError):
                probe.cancel_sequence(offsets, completed, cancel)

    def test_cumulative_budget_counts_requested_path_length_not_net_cancellation(self):
        gesture = {"steps": [{"success_step_offset": i, "operation": {
            "kind": "coordinate", "index": 0, "amount": amount}}
            for i, amount in enumerate([0.2, -0.2])]}
        limits = {**self.limits, "max_total_requested_l2": 0.3}
        with self.assertRaisesRegex(ValueError, "cumulative"):
            probe.make_plan(self.registry, self.evidence(), gesture, limits)
        gesture["cancel_at_offset"] = 0
        with self.assertRaisesRegex(ValueError, "cumulative"):
            probe.make_plan(self.registry, self.evidence(), gesture, limits)

    def test_plans_are_deterministic_and_inputs_are_not_mutated(self):
        before = probe.canonical(self.registry)
        operation = {"kind": "coordinate", "index": 0, "amount": 0.1}
        first, second = self.plan(operation), self.plan(operation)
        self.assertEqual(first["plan_sha256"], second["plan_sha256"])
        self.assertEqual(before, probe.canonical(self.registry))

    def test_output_path_cannot_leave_research_repository(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaisesRegex(ValueError, "research repository"):
            probe.local_path(Path(temporary) / "not-allowed.json")


if __name__ == "__main__":
    unittest.main()
