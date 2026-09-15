import XCTest
@testable import EssentialsCore

final class MechanismTests: XCTestCase {
    func testSplitMixKnownSequenceAndSeededWeights() throws {
        var random = SplitMix64(seed: 0)
        XCTAssertEqual(random.next(), 0xE220A8397B1DCDAF)
        XCTAssertEqual(random.next(), 0x6E789E6AA1B965F4)
        let a = try ReservoirModel(seed: 42)
        let b = try ReservoirModel(seed: 42)
        XCTAssertEqual(a, b)
        for row in 0..<a.nodeCount {
            let sum = a.recurrentWeights[(row * a.nodeCount)..<((row + 1) * a.nodeCount)].reduce(0) { $0 + abs($1) }
            XCTAssertLessThanOrEqual(sum, 0.9 + 1e-12)
        }
    }

    func testRecurrenceUsesPreviousStateBiasThenLeakThenNoise() throws {
        let model = try ReservoirModel(nodeCount: 2, inputCount: 1,
                                       recurrentWeights: [0, 0.5, -0.25, 0],
                                       inputWeights: [0.8, 0.1, -0.3, 0.2])
        var engine = try ReservoirEngine(model: model, leak: 0.4, state: [0.2, -0.4])
        let result = try engine.step(input: [0.5], noise: [0.01, -0.02])
        XCTAssertEqual(result[0], 0.6 * 0.2 + 0.4 * tanh(0.8 * 0.5 + 0.1 - 0.2) + 0.01, accuracy: 1e-14)
        XCTAssertEqual(result[1], 0.6 * -0.4 + 0.4 * tanh(-0.3 * 0.5 + 0.2 - 0.05) - 0.02, accuracy: 1e-14)
        let clipped = try engine.step(input: [0], noise: [10, -10])
        XCTAssertEqual(clipped, [1, -1])
    }

    func testBadInputDoesNotAdvanceStateAndDecodedModelIsValidated() throws {
        var engine = try ReservoirEngine(model: ReservoirModel(seed: 1))
        let before = engine.state
        XCTAssertThrowsError(try engine.step(input: [1]))
        var bad = [Double](repeating: 0, count: 66); bad[5] = .nan
        XCTAssertThrowsError(try engine.step(input: bad))
        XCTAssertEqual(engine.state, before)
        let invalid = Data("{\"nodeCount\":2,\"inputCount\":1,\"recurrentWeights\":[0],\"inputWeights\":[0,0,0,0]}".utf8)
        XCTAssertThrowsError(try JSONDecoder().decode(ReservoirModel.self, from: invalid))
    }

    func testSensoryRankOneUpdateAndEigenvectorResidual() throws {
        var field = try SensoryField(dimension: 2, inputCount: 2, projection: [1, 0, 0, 1])
        let measurement = try field.step(input: [1, 0], retention: 0.5)
        XCTAssertEqual(measurement.fieldVector[0], sqrt(2), accuracy: 1e-14)
        XCTAssertEqual(measurement.covariance[0], 1.5, accuracy: 1e-14)
        XCTAssertEqual(measurement.covariance[3], 0.5, accuracy: 1e-14)
        XCTAssertEqual(measurement.eigenvalues[0], 1.5, accuracy: 1e-14)
        for mode in 0..<2 { for row in 0..<2 {
            let av = (0..<2).reduce(0.0) { $0 + measurement.covariance[row * 2 + $1] * measurement.eigenvectors[mode * 2 + $1] }
            XCTAssertEqual(av, measurement.eigenvalues[mode] * measurement.eigenvectors[mode * 2 + row], accuracy: 1e-12)
        } }
        let quiet = try field.step(input: [0, 0], retention: 0.5)
        XCTAssertEqual(quiet.covariance[0], 0.75, accuracy: 1e-14)
        XCTAssertEqual(quiet.fieldVector, [0, 0])
    }

    func testDisplaySummaryIsEightModesWhileFillUsesAllModes() {
        let flat = SensoryField.summary(eigenvalues: [Double](repeating: 1, count: 32))
        XCTAssertEqual(flat.entropy, 1, accuracy: 1e-14)
        XCTAssertEqual(flat.head, 0.125, accuracy: 1e-14)
        XCTAssertEqual(flat.shoulder, 0.25, accuracy: 1e-14)
        XCTAssertEqual(flat.tail, 0.625, accuracy: 1e-14)
        let concentrated = SensoryField.summary(eigenvalues: [10, 0, 0, 0])
        XCTAssertEqual(concentrated.entropy, 0)
        XCTAssertEqual(concentrated.head, 1)
        var first = ReducedFill(), scaled = ReducedFill(), rankOne = ReducedFill()
        let spectrum = [Double](repeating: 1, count: 16) + [Double](repeating: 0, count: 16)
        XCTAssertEqual(first.update(eigenvalues: spectrum), 0.05, accuracy: 1e-14)
        XCTAssertEqual(scaled.update(eigenvalues: spectrum.map { $0 * 100 }), 0.05, accuracy: 1e-14)
        XCTAssertEqual(rankOne.update(eigenvalues: [32] + [Double](repeating: 0, count: 31)), 0.004, accuracy: 1e-14)
    }

    func testCodecIsFiniteDeterministicAndDoesNotInventEmbedding() {
        let text = "I wonder how this warm field changes. Perhaps we can explore it together? 🌱"
        let a = TextCodec.encode(text), b = TextCodec.encode(text)
        XCTAssertEqual(a, b)
        XCTAssertEqual(a.count, 48)
        XCTAssertTrue(a.allSatisfy(\.isFinite))
        XCTAssertTrue(a.prefix(32).allSatisfy { abs($0) <= 5 })
        XCTAssertEqual(Array(a.suffix(16)), [Double](repeating: 0, count: 16))
        XCTAssertGreaterThan(a[18], 0)
        XCTAssertGreaterThan(a[24], 0)
        XCTAssertGreaterThan(a[26], 0)
        XCTAssertEqual(TextCodec.encode("\n  "), [Double](repeating: 0, count: 48))
    }

    func testControllerDirectionSlewDeadbandAndBounds() throws {
        var high = RetentionController(), low = RetentionController(), band = RetentionController()
        XCTAssertEqual(high.update(fillPct: 90).appliedRetention, 0.945, accuracy: 1e-14)
        XCTAssertEqual(low.update(fillPct: 20).appliedRetention, 0.965, accuracy: 1e-14)
        XCTAssertEqual(band.update(fillPct: 69).appliedRetention, 0.955, accuracy: 1e-14)
        var prior = high.currentRetention
        for _ in 0..<200 {
            let next = high.update(fillPct: 100)
            XCTAssertLessThanOrEqual(abs(next.appliedRetention - prior), 0.01 + 1e-14)
            XCTAssertTrue((0.82...0.995).contains(next.appliedRetention))
            XCTAssertLessThanOrEqual(abs(next.integral), 1)
            prior = next.appliedRetention
        }
        XCTAssertThrowsError(try RetentionController(initialRetention: .nan))
    }

    func testRegulatorChangesRealFieldWithSameForcing() throws {
        var open = try SensoryField(seed: 98), closed = try SensoryField(seed: 98)
        var openFill = ReducedFill(), closedFill = ReducedFill(), control = RetentionController()
        var random = SplitMix64(seed: 42)
        var openError = 0.0, closedError = 0.0
        var openValues: [Double] = [], closedValues: [Double] = [], retained: [Double] = []
        for tick in 0..<600 {
            let input = (0..<66).map { _ in random.nextSigned() }
            let ordinary = try open.step(input: input)
            let regulated = try closed.step(input: input, retention: control.currentRetention)
            let f1 = openFill.update(eigenvalues: ordinary.eigenvalues) * 100
            let f2 = closedFill.update(eigenvalues: regulated.eigenvalues) * 100
            control.update(fillPct: f2)
            if tick >= 300 {
                openError += abs(f1 - 68); closedError += abs(f2 - 68)
                openValues.append(f1); closedValues.append(f2); retained.append(control.currentRetention)
            }
        }
        XCTAssertLessThan(closedError, openError)
        XCTAssertNotEqual(open.covariance, closed.covariance)
        let report: [String: Any] = [
            "schema": "essentials.regulation_qualification.v1", "fixture": "independent_seeded_uniform_66d_inputs",
            "field_dimension": 32, "input_dimension": 66, "field_seed": 98, "input_seed": 42,
            "random_generator": "SplitMix64", "step_count": 600, "dt_seconds": 1.0 / 3.0,
            "evaluation_steps_inclusive": [301, 600], "evaluation_n": 300,
            "target_fill_pct": 68.0, "target_deadband_pct": 4.0,
            "common_forcing": true, "only_intervention": "covariance_retention_controller",
            "baseline": ["retention": 0.955, "mean_fill_pct": openValues.reduce(0, +) / 300,
                         "mean_absolute_target_error_pct": openError / 300,
                         "minimum_fill_pct": openValues.min()!, "maximum_fill_pct": openValues.max()!],
            "regulated": ["mean_fill_pct": closedValues.reduce(0, +) / 300,
                          "mean_absolute_target_error_pct": closedError / 300,
                          "minimum_fill_pct": closedValues.min()!, "maximum_fill_pct": closedValues.max()!,
                          "minimum_retention": retained.min()!, "maximum_retention": retained.max()!],
            "passes_lower_absolute_target_error": closedError < openError,
            "actual_covariance_differs": open.covariance != closed.covariance,
            "scope": "Synthetic reduced-model qualification; not production parity or guaranteed target attainment."
        ]
        let json = try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys])
        print("ESSENTIALS_REGULATION_QUALIFICATION " + String(decoding: json, as: UTF8.self))
    }

    func testConstantDirectionAndZeroInputCannotManufactureTargetRank() throws {
        var projection = [Double](repeating: 0, count: 32 * 66)
        projection[0] = 1
        var rankOneCovariance = [Double](repeating: 0, count: 32 * 32)
        rankOneCovariance[0] = 32
        var constant = try SensoryField(dimension: 32, inputCount: 66, projection: projection, covariance: rankOneCovariance)
        var zero = try SensoryField(dimension: 32, inputCount: 66, projection: projection,
                                    covariance: [Double](repeating: 0, count: 32 * 32))
        var constantFill = ReducedFill(), zeroFill = ReducedFill()
        var constantControl = RetentionController(), zeroControl = RetentionController()
        var input = [Double](repeating: 0, count: 66); input[0] = 1
        for _ in 0..<120 {
            let first = try constant.step(input: input, retention: constantControl.currentRetention)
            let second = try zero.step(input: [Double](repeating: 0, count: 66), retention: zeroControl.currentRetention)
            constantControl.update(fillPct: 100 * constantFill.update(eigenvalues: first.eigenvalues))
            zeroControl.update(fillPct: 100 * zeroFill.update(eigenvalues: second.eigenvalues))
            XCTAssertEqual(first.eigenvalues.filter { $0 > 0.12 }.count, 1)
            XCTAssertTrue(second.covariance.allSatisfy { $0 == 0 })
        }
        XCTAssertLessThan(constantFill.fill * 100, 5)
        XCTAssertEqual(zeroFill.fill, 0)
        XCTAssertEqual(constantControl.currentRetention, 0.995, accuracy: 1e-14)
        XCTAssertEqual(zeroControl.currentRetention, 0.995, accuracy: 1e-14)
        let report: [String: Any] = [
            "schema": "essentials.unreachable_rank_qualification.v1", "step_count": 120,
            "constant_direction": ["final_fill_pct": constantFill.fill * 100, "rank": 1,
                                    "retention_at_upper_bound": constantControl.currentRetention],
            "zero_input_and_covariance": ["final_fill_pct": zeroFill.fill * 100,
                                          "retention_at_upper_bound": zeroControl.currentRetention],
            "outcome": "Target remains unreachable; controller does not invent input, spectral rank, or displayed fill."
        ]
        let json = try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys])
        print("ESSENTIALS_UNREACHABLE_QUALIFICATION " + String(decoding: json, as: UTF8.self))
    }
}
