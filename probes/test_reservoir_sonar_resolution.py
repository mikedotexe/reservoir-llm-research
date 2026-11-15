"""Analytic counterexamples and replay-boundary checks for the offline scanner."""
import copy
import unittest

import numpy as np

from compact_reservoir_sonar import calibrate
from refine_reservoir_sonar import Frozen, coordinate_maps, metrics


def fixture():
    return Frozen(dict(seed="20260909", rngState="1234567", step=13,
                       controls=dict(leak=.65, recurrentGain=1, feedbackScale=.5),
                       heldVector=[0.0] * 48, state=[.2] * 32,
                       noiseAmplitude=.02, dt=.1))


class ResponseQualificationTests(unittest.TestCase):
    def test_analytic_decoupled_recurrence_has_known_signed_impulse_path(self):
        engine = fixture()
        engine.a = .5
        engine.w[:] = 0
        engine.win[:] = 0
        engine.b = engine.win[:, 18:66]
        engine.b[:, :32] = np.eye(32)
        engine.origin.update(state=[0.0] * 32, noiseAmplitude=0)
        pulse = np.zeros((2, 48)); pulse[0, 7] = .07; pulse[1, 7] = -.07
        paths, _ = engine.rollout(pulse, 8)
        expected = .5 * np.tanh(.07) * .5 ** np.arange(8)
        np.testing.assert_allclose(paths[0, :, 7], expected, atol=1e-16)
        np.testing.assert_allclose(paths[1, :, 7], -expected, atol=1e-16)
        self.assertEqual(np.count_nonzero(paths[:, :, np.arange(32) != 7]), 0)

    def test_split_continuation_preserves_rng_phase_and_state(self):
        engine = fixture()
        original = copy.deepcopy(engine.origin)
        whole, _ = engine.rollout(np.zeros((1, 48)), 30)
        tail, _ = engine.at_offset(12).rollout(np.zeros((1, 48)), 18)
        np.testing.assert_array_equal(tail[0], whole[0, 12:])
        self.assertEqual(original, engine.origin)

    def test_zero_leak_produces_no_input_signal(self):
        engine = fixture(); engine.a = 0
        matrices, _, _ = coordinate_maps(engine, .001, 4)
        np.testing.assert_array_equal(matrices, np.zeros_like(matrices))
        result = metrics(np.zeros((64, 32)), np.zeros((64, 32)))
        self.assertIsNone(result["aggregateRelativeError"])
        self.assertEqual(result["resolvedDirections"], 0)

    def test_exact_clipping_boundary_defeats_a_single_linear_map(self):
        # At y=1, one sign is clipped while the other moves. Smallness alone does
        # not make a two-sided linear model valid; the predictive check must fail.
        engine = fixture(); engine.a = 1
        engine.w[:] = 0; engine.win[:] = 0
        engine.b = engine.win[:, 18:66]
        engine.origin["state"] = [0.0] * 32
        _, noise, _ = engine.inputs(1)
        row = int(np.argmax(noise[0]))
        self.assertGreater(noise[0, row], 0)
        engine.win[row, 66] = np.arctanh(1 - noise[0, row])
        engine.b[row, 0] = 1
        impulses = np.zeros((2, 48)); impulses[:, 0] = [.001, -.001]
        base, _ = engine.rollout(np.zeros((1, 48)), 1)
        actual, _ = engine.rollout(impulses, 1)
        matrix, _, _ = coordinate_maps(engine, .001, 1)
        observed = actual[:, 0] - base[0, 0]
        result = metrics(impulses @ matrix[0].T, observed)
        self.assertGreater(result["aggregateRelativeError"], .6)
        self.assertAlmostEqual(observed[0, row], 0, places=14)
        self.assertLess(observed[1, row], 0)

    def test_compact_calibration_rejects_unobservable_wiring(self):
        engine = fixture(); engine.b[0] = 0
        # A zero row has no gain to identify. This implementation rejects rather
        # than silently dividing by zero or inventing a sensitivity.
        candidates = np.ones((2, 48)) / np.sqrt(48)
        with np.errstate(invalid="ignore"):
            with self.assertRaises(ValueError):
                calibrate(engine, candidates)


if __name__ == "__main__":
    unittest.main()
