import XCTest
@testable import EssentialsCore

final class TeachingExampleTests: XCTestCase, @unchecked Sendable {
    private func run(_ spec: ActionComparisonSpecification) async throws -> ActionComparisonRecord {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("teaching-example-\(UUID())")
        defer { try? FileManager.default.removeItem(at: directory) }
        return try await ActionComparisonSession(specification: spec,
            journalStore: LocalActionJournalStore(directory: directory)).run()
    }
    private func object(_ record: ActionComparisonRecord) throws -> [String: Any] {
        try JSONSerialization.jsonObject(with: JSONEncoder().encode(record)) as! [String: Any]
    }
    private func decode(_ object: [String: Any]) throws -> ActionComparisonRecord {
        try JSONDecoder().decode(ActionComparisonRecord.self, from: JSONSerialization.data(withJSONObject: object))
    }

    func testLegacyPulseIsUnchangedAndContinuousProfileOnlyRemovesEnvelope() throws {
        for step in 1...120 {
            let pulse = ActionForcingProfile.pulsedSensoryV1.input(step: step)
            let continuous = ActionForcingProfile.continuousSensoryV1.input(step: step)
            XCTAssertEqual(pulse, Recipe.forcing(step: step, dt: 1.0 / 3.0))
            XCTAssertTrue(continuous.suffix(50).allSatisfy { $0 == 0 })
            if (step - 1) % 30 < 12 { XCTAssertEqual(pulse, continuous) }
            else { XCTAssertTrue(pulse.allSatisfy { $0 == 0 }); XCTAssertTrue(continuous.prefix(16).contains { $0 != 0 }) }
        }
        let decoded = try JSONDecoder().decode(ActionComparisonSpecification.self, from: Data("{}".utf8))
        XCTAssertEqual(decoded.forcingProfile, .pulsedSensoryV1)
        var invalid = ActionComparisonSpecification(forcingProfile: .continuousSensoryV1)
        XCTAssertThrowsError(try invalid.validate())
        invalid.comparisonKind = .observation; invalid.stage = .journalOutput; invalid.mode = .independentGeneration
        XCTAssertNoThrow(try invalid.validate())
        XCTAssertThrowsError(try JSONDecoder().decode(ActionComparisonSpecification.self,
            from: Data("{\"forcingProfile\":\"unknown-profile\"}".utf8)))
    }

    func testActiveObservationIsMatchedAtAllThreeFixedOpportunities() async throws {
        let spec = ActionComparisonSpecification(stage: .journalOutput, mode: .independentGeneration, steps: 120,
            comparisonKind: .observation, forcingProfile: .continuousSensoryV1)
        let record = try await run(spec)
        XCTAssertEqual(record.format, ActionComparisonRecord.currentFormat)
        XCTAssertEqual(record.right.actions.map(\.observedStep), [30, 60, 90])
        XCTAssertEqual(record.left!.actions.map(\.requestOrder), [1, 2, 1])
        XCTAssertEqual(record.right.actions.map(\.requestOrder), [2, 1, 2])
        XCTAssertEqual(record.left!.frames.map(\.state), record.right.frames.map(\.state))
        XCTAssertEqual(record.left!.frames.map(\.input), record.right.frames.map(\.input))
        XCTAssertEqual(record.left!.frames.map { $0.spectral!.eigenvalues }, record.right.frames.map { $0.spectral!.eigenvalues })
        for step in [30, 60, 90] {
            let frame = record.right.frames[step - 1]
            XCTAssertGreaterThanOrEqual(frame.state.map(abs).max()!, 0.25)
            XCTAssertTrue(frame.semanticInput.allSatisfy { $0 == 0 })
        }
        XCTAssertEqual(try record.verify().checkedSteps, 240)
        for format in [ActionComparisonRecord.previousFormat, ActionComparisonRecord.legacyFormat] {
            var json = try object(record); json["format"] = format
            XCTAssertThrowsError(try decode(json).verify(), "Nonlegacy forcing under \(format)")
        }
        var json = try object(record), specification = json["specification"] as! [String: Any]
        specification.removeValue(forKey: "forcingProfile"); json["specification"] = specification
        XCTAssertThrowsError(try decode(json).verify(), "Deleting continuous input metadata must not reinterpret the trajectory.")
    }

    func testV2ReplayKeepsItsOriginalPromptAndImplicitPulse() async throws {
        let record = try await run(ActionComparisonSpecification(stage: .journalOutput, steps: 31))
        var json = try object(record), specification = json["specification"] as! [String: Any]
        json["format"] = ActionComparisonRecord.previousFormat
        specification.removeValue(forKey: "forcingProfile"); json["specification"] = specification
        let legacy = try decode(json)
        XCTAssertEqual(legacy.specification.promptVersion, 2)
        XCTAssertEqual(legacy.right.actions[0].prompt, record.right.actions[0].prompt)
        XCTAssertEqual(try legacy.verify().checkedSteps, 62)
    }

    func testV1ReplayRetainsOriginalPromptVerification() async throws {
        let record = try await run(ActionComparisonSpecification(stage: .journalOutput, steps: 31, promptVersion: 1))
        var json = try object(record), specification = json["specification"] as! [String: Any]
        json["format"] = ActionComparisonRecord.legacyFormat
        for key in ["forcingProfile", "promptVersion", "comparisonKind"] { specification.removeValue(forKey: key) }
        json["specification"] = specification
        for arm in ["left", "right"] {
            var value = json[arm] as! [String: Any]
            value.removeValue(forKey: "observationChannel"); json[arm] = value
        }
        let legacy = try decode(json)
        XCTAssertEqual(legacy.specification.promptVersion, 1)
        XCTAssertEqual(legacy.right.actions[0].prompt, record.right.actions[0].prompt)
        XCTAssertEqual(try legacy.verify().checkedSteps, 62)
    }
}

final class RegulationExampleTests: XCTestCase {
    private static let fixture = try! RegulationExampleRecord.generate()
    private func replacing(frames: [RegulationExampleFrame]? = nil, summary: RegulationExampleSummary? = nil) -> RegulationExampleRecord {
        let r = Self.fixture
        return RegulationExampleRecord(format: r.format, specification: r.specification, projectionWeights: r.projectionWeights,
                                       frames: frames ?? r.frames, summary: summary ?? r.summary)
    }
    func testKnownControllerCaseReproducesItsDeclaredWindowAndEffect() throws {
        let r = Self.fixture, s = r.summary
        XCTAssertEqual(r.frames.count, 600)
        XCTAssertEqual(s.evaluationFirstStep, 301); XCTAssertEqual(s.evaluationLastStep, 600); XCTAssertEqual(s.evaluationCount, 300)
        XCTAssertEqual(s.baselineMeanAbsoluteError, 11.924755885049208, accuracy: 1e-8)
        XCTAssertEqual(s.regulatedMeanAbsoluteError, 4.159937143601516, accuracy: 1e-8)
        XCTAssertLessThan(s.regulatedMeanAbsoluteError, s.baselineMeanAbsoluteError)
        XCTAssertEqual(try r.verify().checkedSteps, 1200)
    }
    func testInputsAreFullDimensionalAndControlAppliesOnlyOnNextStep() throws {
        let r = Self.fixture
        XCTAssertTrue(r.frames[0].input.suffix(48).contains { $0 != 0 })
        XCTAssertEqual(r.frames[0].baseline.spectral, r.frames[0].regulated.spectral)
        XCTAssertEqual(r.frames[0].regulated.retentionUsed, 0.955)
        for (previous, next) in zip(r.frames, r.frames.dropFirst()) {
            XCTAssertNil(next.baseline.control)
            XCTAssertEqual(next.baseline.retentionUsed, 0.955)
            XCTAssertEqual(next.regulated.retentionUsed, previous.regulated.control!.appliedRetention)
        }
        XCTAssertNotEqual(r.frames[1].baseline.spectral.covariance, r.frames[1].regulated.spectral.covariance)
    }
    func testChangedInputsAndEarlyApplicationAreRejected() throws {
        let r = Self.fixture, first = r.frames[0]
        var changed = r.frames, input = first.input; input[65] += 0.01
        changed[0] = RegulationExampleFrame(step: first.step, time: first.time, input: input,
                                           baseline: first.baseline, regulated: first.regulated)
        XCTAssertThrowsError(try replacing(frames: changed).verify())
        let early = RegulationArmFrame(spectral: first.regulated.spectral, fillPercent: first.regulated.fillPercent,
            retentionUsed: first.regulated.control!.appliedRetention, control: first.regulated.control)
        changed[0] = RegulationExampleFrame(step: first.step, time: first.time, input: first.input,
                                           baseline: first.baseline, regulated: early)
        XCTAssertThrowsError(try replacing(frames: changed).verify())
    }
    func testChangedWindowSummaryAndDroppedOpportunityAreRejected() throws {
        let r = Self.fixture, s = r.summary
        let altered = RegulationExampleSummary(evaluationFirstStep: 302, evaluationLastStep: 600, evaluationCount: 299,
            baselineMeanAbsoluteError: s.baselineMeanAbsoluteError, regulatedMeanAbsoluteError: s.regulatedMeanAbsoluteError,
            baselineMeanFillPercent: s.baselineMeanFillPercent, regulatedMeanFillPercent: s.regulatedMeanFillPercent,
            regulatedMinimumRetention: s.regulatedMinimumRetention, regulatedMaximumRetention: s.regulatedMaximumRetention)
        XCTAssertThrowsError(try replacing(summary: altered).verify())
        XCTAssertThrowsError(try replacing(frames: Array(r.frames.dropLast())).validateStructure())
        for setting in ["{\"fieldSeed\":99}", "{\"inputSeed\":43}", "{\"steps\":120}", "{\"evaluationFirstStep\":302}"] {
            let spec = try JSONDecoder().decode(RegulationExampleSpecification.self, from: Data(setting.utf8))
            XCTAssertThrowsError(try spec.validate())
        }
    }
    func testPortableRoundTripReplaysWithoutOriginalLocation() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("regulation-portability-\(UUID())")
        defer { try? FileManager.default.removeItem(at: directory) }
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let original = directory.appendingPathComponent("original.json"), moved = directory.appendingPathComponent("moved.json")
        try Self.fixture.write(to: original)
        try FileManager.default.moveItem(at: original, to: moved)
        let loaded = try RegulationExampleRecord.read(from: moved)
        XCTAssertEqual(try loaded.verify().checkedSteps, 1200)
        XCTAssertEqual(loaded.frames[599].input, Self.fixture.frames[599].input)
    }
}
