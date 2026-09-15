import XCTest
@testable import EssentialsCore

final class ExplorationTests: XCTestCase {
    func testDefaultExplorationIsExactlyQuietWithoutHiddenPulseOrBias() throws {
        var engine = try ExplorationEngine()
        XCTAssertTrue(engine.frames.isEmpty)
        for step in 1...8 {
            let frame = try engine.advance(controls: ExplorationControls())
            XCTAssertEqual(frame.step, step)
            XCTAssertEqual(frame.time, Double(step) / 3, accuracy: 1e-14)
            XCTAssertFalse(frame.pulse)
            for values in [frame.input, frame.previousState, frame.inputDrive, frame.recurrentDrive,
                           frame.biasDrive, frame.proposal, frame.state, frame.noise] {
                XCTAssertTrue(values.allSatisfy { $0 == 0 })
            }
            XCTAssertNil(frame.spectral)
        }
    }

    func testRecurrenceOffDecaysAndOnUsesPreviousState() throws {
        var off = try ExplorationEngine(seed: 42), on = try ExplorationEngine(seed: 42)
        let quiet = ExplorationControls()
        let recurrent = ExplorationControls(recurrenceEnabled: true)
        let initialOff = try off.advance(controls: quiet, pulse: true)
        let initialOn = try on.advance(controls: recurrent, pulse: true)
        XCTAssertEqual(initialOff.state, initialOn.state)
        let offNext = try off.advance(controls: quiet)
        let onNext = try on.advance(controls: recurrent)
        XCTAssertTrue(offNext.recurrentDrive.allSatisfy { $0 == 0 })
        XCTAssertTrue(onNext.recurrentDrive.contains { abs($0) > 1e-12 })
        for index in 0..<32 {
            XCTAssertEqual(offNext.state[index], 0.35 * initialOff.state[index], accuracy: 1e-14)
            XCTAssertLessThanOrEqual(abs(onNext.recurrentDrive[index]), 0.9 + 1e-14)
        }
        XCTAssertNotEqual(offNext.state, onNext.state)
    }

    func testContributionsReconstructControlledHandUpdate() throws {
        var engine = try ExplorationEngine(seed: 111)
        try engine.advance(controls: ExplorationControls(), pulse: true)
        let controls = ExplorationControls(leak: 0.4, recurrenceEnabled: true, recurrenceStrength: 0.7,
                                           inputStrength: 0.6, noiseAmplitude: 0.13, biasEnabled: true)
        let frame = try engine.advance(controls: controls, pulse: true)
        for row in 0..<32 {
            let input = (0..<66).reduce(0.0) { $0 + engine.model.inputWeights[row * 67 + $1] * frame.input[$1] }
            let recurrence = (0..<32).reduce(0.0) {
                $0 + engine.model.recurrentWeights[row * 32 + $1] * 0.7 * frame.previousState[$1]
            }
            let bias = engine.model.inputWeights[row * 67 + 66]
            XCTAssertEqual(frame.inputDrive[row], input, accuracy: 1e-14)
            XCTAssertEqual(frame.recurrentDrive[row], recurrence, accuracy: 1e-14)
            XCTAssertEqual(frame.biasDrive[row], bias, accuracy: 1e-14)
            XCTAssertEqual(frame.proposal[row], tanh(input + recurrence + bias), accuracy: 1e-14)
            let next = min(1, max(-1, 0.6 * frame.previousState[row] + 0.4 * frame.proposal[row] + frame.noise[row]))
            XCTAssertEqual(frame.state[row], next, accuracy: 1e-14)
            XCTAssertLessThanOrEqual(abs(frame.noise[row]), 0.13)
        }
        XCTAssertEqual(engine.model, try ReservoirModel(seed: 111))
    }

    func testSinglePulseAndRepeatingExternalInputHaveDistinctRecordedTiming() throws {
        var single = try ExplorationEngine(seed: 99), repeating = try ExplorationEngine(seed: 99)
        let pulse = try single.advance(controls: ExplorationControls(), pulse: true)
        let repeatControls = ExplorationControls(repeatInput: true)
        let firstRepeat = try repeating.advance(controls: repeatControls)
        XCTAssertEqual(pulse.input, firstRepeat.input)
        XCTAssertTrue(try single.advance(controls: ExplorationControls()).input.allSatisfy { $0 == 0 })
        let second = try repeating.advance(controls: repeatControls)
        XCTAssertNotEqual(firstRepeat.input, second.input)
        for step in 3...31 {
            let frame = try repeating.advance(controls: repeatControls)
            XCTAssertTrue(frame.input[18..<66].allSatisfy { $0 == 0 })
            if (13...30).contains(step) { XCTAssertTrue(frame.input.allSatisfy { $0 == 0 }) }
            if step == 31 { XCTAssertTrue(frame.input.contains { $0 != 0 }) }
        }
        let override = try repeating.advance(controls: ExplorationControls(inputStrength: 0.25), pulse: true)
        for index in 0..<66 { XCTAssertEqual(override.input[index], pulse.input[index] * 0.25, accuracy: 1e-14) }
    }

    func testLiveLeakNoiseAndValidationDoNotShiftRandomStream() throws {
        var first = try ExplorationEngine(seed: 8), second = try ExplorationEngine(seed: 8)
        try first.advance(controls: ExplorationControls())
        try second.advance(controls: ExplorationControls(noiseAmplitude: 0.2))
        let noised = ExplorationControls(leak: 0, noiseAmplitude: 0.1)
        var invalid = noised; invalid.inputStrength = .nan
        XCTAssertThrowsError(try first.advance(controls: invalid))
        XCTAssertEqual(first.frames.count, 1)
        let a = try first.advance(controls: noised, pulse: true)
        let b = try second.advance(controls: noised)
        XCTAssertEqual(a.noise, b.noise) // First step consumed samples even at zero amplitude.
        XCTAssertEqual(a.state, a.noise) // Leak zero prevents the pulse entering state.
        let full = try first.advance(controls: ExplorationControls(leak: 1), pulse: true)
        XCTAssertEqual(full.state, full.proposal)
    }

    func testSensoryRisingEdgeStartsFreshAndOffHasNoMeasurement() throws {
        var engine = try ExplorationEngine(seed: 51)
        let enabled = ExplorationControls(sensoryEnabled: true, retention: 0.9)
        let first = try engine.advance(controls: enabled, pulse: true)
        let second = try engine.advance(controls: enabled, pulse: true)
        XCTAssertNotEqual(first.spectral?.covariance, second.spectral?.covariance)
        XCTAssertNil(try engine.advance(controls: ExplorationControls()).spectral)
        let reset = try engine.advance(controls: enabled, pulse: true)
        XCTAssertEqual(first.spectral?.covariance, reset.spectral?.covariance)
        XCTAssertEqual(first.spectral?.fieldVector, reset.spectral?.fieldVector)
        XCTAssertEqual(try engine.record.verify().checkedSteps, 4)
    }

    func testRoundTripAndResumptionPreserveControlsFieldStateAndNoise() throws {
        var engine = try ExplorationEngine(seed: 93)
        for step in 0..<14 {
            let controls = ExplorationControls(leak: step < 5 ? 0.3 : 0.7, recurrenceEnabled: step > 2,
                recurrenceStrength: 0.6, repeatInput: step % 3 == 0, inputStrength: 0.4,
                noiseAmplitude: step > 8 ? 0.04 : 0, biasEnabled: step == 4,
                sensoryEnabled: step % 4 != 0, retention: 0.92)
            try engine.advance(controls: controls, pulse: step == 7)
        }
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let file = directory.appendingPathComponent("exploration.json")
        try engine.record.write(to: file)
        let decoded = try ExplorationRecord.read(from: file)
        XCTAssertEqual(decoded.format, "essentials-exploration-v1")
        XCTAssertEqual(try decoded.verify().checkedSteps, 14)
        var restored = try ExplorationEngine(record: decoded)
        for step in 0..<8 {
            let controls = ExplorationControls(recurrenceEnabled: true, repeatInput: true,
                                               noiseAmplitude: 0.03, sensoryEnabled: step < 4, retention: 0.96)
            let a = try engine.advance(controls: controls, pulse: step == 3)
            let b = try restored.advance(controls: controls, pulse: step == 3)
            XCTAssertEqual(a.input, b.input); XCTAssertEqual(a.noise, b.noise)
            XCTAssertEqual(a.state, b.state); XCTAssertEqual(a.inputDrive, b.inputDrive)
            XCTAssertEqual(a.spectral, b.spectral)
        }
    }

    func testVerifierRejectsTamperingAcrossControlsContributionsAndSpectra() throws {
        var engine = try ExplorationEngine(seed: 7)
        try engine.advance(controls: ExplorationControls(recurrenceEnabled: true, sensoryEnabled: true), pulse: true)
        let original = try JSONSerialization.jsonObject(with: JSONEncoder().encode(engine.record)) as! [String: Any]
        func tampered(_ update: (inout [String: Any]) -> Void) throws -> ExplorationRecord {
            var object = original; update(&object)
            return try JSONDecoder().decode(ExplorationRecord.self, from: JSONSerialization.data(withJSONObject: object))
        }
        for key in ["state", "inputDrive", "recurrentDrive", "biasDrive", "proposal", "noise", "input"] {
            let bad = try tampered { object in
                var frames = object["frames"] as! [[String: Any]]
                var values = frames[0][key] as! [Double]; values[0] += 0.1
                frames[0][key] = values; object["frames"] = frames
            }
            XCTAssertThrowsError(try bad.verify(), key)
        }
        let wrongShape = try tampered { object in
            var frames = object["frames"] as! [[String: Any]]
            frames[0]["state"] = [0]; object["frames"] = frames
        }
        XCTAssertThrowsError(try wrongShape.verify())
        let wrongBasis = try tampered { object in
            var frames = object["frames"] as! [[String: Any]]
            var spectral = frames[0]["spectral"] as! [String: Any]
            spectral["eigenvectors"] = [Double](repeating: 0, count: 1024)
            frames[0]["spectral"] = spectral; object["frames"] = frames
        }
        XCTAssertThrowsError(try wrongBasis.verify())
        let wrongControl = try tampered { object in
            var frames = object["frames"] as! [[String: Any]]
            var controls = frames[0]["controls"] as! [String: Any]; controls["leak"] = 0.1
            frames[0]["controls"] = controls; object["frames"] = frames
        }
        XCTAssertThrowsError(try wrongControl.verify())
        let wrongSeed = try tampered { $0["seed"] = 17 }
        XCTAssertThrowsError(try wrongSeed.verify())
    }

    func testStepCapAndEmptyRecordAreExplicit() throws {
        var engine = try ExplorationEngine(seed: 1)
        XCTAssertEqual(try engine.record.verify().checkedSteps, 0)
        for _ in 0..<ExplorationEngine.maximumSteps { try engine.advance(controls: ExplorationControls()) }
        XCTAssertThrowsError(try engine.advance(controls: ExplorationControls(), pulse: true))
        XCTAssertEqual(engine.frames.count, 1800)
        XCTAssertEqual(engine.frames.last?.step, 1800)
    }

    func testImportKeepsStoredValidEigenvectorOrientation() throws {
        var engine = try ExplorationEngine(seed: 13)
        try engine.advance(controls: ExplorationControls(sensoryEnabled: true), pulse: true)
        var object = try JSONSerialization.jsonObject(with: JSONEncoder().encode(engine.record)) as! [String: Any]
        var frames = object["frames"] as! [[String: Any]]
        var spectral = frames[0]["spectral"] as! [String: Any]
        var vectors = spectral["eigenvectors"] as! [Double]
        for index in 0..<32 { vectors[index] = -vectors[index] }
        spectral["eigenvectors"] = vectors; frames[0]["spectral"] = spectral; object["frames"] = frames
        let imported = try JSONDecoder().decode(ExplorationRecord.self, from: JSONSerialization.data(withJSONObject: object))
        XCTAssertEqual(try imported.verify().checkedSteps, 1)
        let resumed = try ExplorationEngine(record: imported)
        XCTAssertEqual(resumed.record.frames[0].spectral?.eigenvectors, vectors)
    }
}
