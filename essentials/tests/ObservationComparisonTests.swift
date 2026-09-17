import XCTest
@testable import EssentialsCore

final class ObservationComparisonTests: XCTestCase, @unchecked Sendable {
    private func session(backend: any LanguageBackend = ScriptedActionLanguageBackend()) throws -> ActionComparisonSession {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("observation-test-\(UUID())")
        addTeardownBlock { try? FileManager.default.removeItem(at: directory) }
        let spec = ActionComparisonSpecification(stage: .journalOutput, mode: .independentGeneration,
            steps: 65, comparisonKind: .observation)
        return try ActionComparisonSession(specification: spec, journalStore: LocalActionJournalStore(directory: directory), backend: backend)
    }
    func testObservationOnlyChangesAccessAndAlternatesActualRequestOrder() async throws {
        let run = try await session().run()
        XCTAssertEqual(run.format, "essentials-actions-v3")
        XCTAssertEqual(run.left!.frames.map(\.state), run.right.frames.map(\.state))
        XCTAssertEqual(run.left!.frames.map(\.input), run.right.frames.map(\.input))
        XCTAssertEqual(run.left!.actions.map(\.requestOrder), [1, 2])
        XCTAssertEqual(run.right.actions.map(\.requestOrder), [2, 1])
        XCTAssertEqual(run.left!.observationChannel, .sensory)
        XCTAssertEqual(run.right.observationChannel, .sensoryAndReservoir)
        for (a,b) in zip(run.left!.actions, run.right.actions) {
            XCTAssertFalse(a.prompt.contains("x[0]="))
            XCTAssertTrue(b.prompt.hasPrefix(a.prompt))
            XCTAssertTrue(b.prompt.contains("x[31]="))
            XCTAssertTrue(b.prompt.contains("observation at step \(b.observedStep)"))
            XCTAssertNil(b.applicationStep); XCTAssertNil(b.memoryText)
        }
        XCTAssertEqual(try run.verify().checkedSteps, 130)
    }
    func testOneArmFailureDoesNotEraseOrSkipItsPartner() async throws {
        let run = try await session(backend: FailSensoryBackend()).run()
        XCTAssertEqual(run.status, .failed)
        XCTAssertEqual(run.left!.actions.count, 1); XCTAssertEqual(run.right.actions.count, 1)
        XCTAssertEqual(run.left!.actions[0].status, .failed)
        XCTAssertEqual(run.right.actions[0].status, .completed)
        XCTAssertEqual(run.right.journals.count, 1)
        try run.verify()
    }
    func testTamperedChannelsCoordinatesOrderAndVersionAreRejected() async throws {
        let run = try await session().run()
        let data = try JSONEncoder().encode(run)
        for mutation in 0..<6 {
            var json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
            var right = json["right"] as! [String: Any]
            var actions = right["actions"] as! [[String: Any]]
            if mutation == 0 { right["observationChannel"] = "sensory" }
            if mutation == 1 { actions[0]["prompt"] = (actions[0]["prompt"] as! String).replacingOccurrences(of: "x[31]=", with: "x[32]=") }
            if mutation == 2 { actions[0]["requestOrder"] = 1 }
            if mutation == 3 { json["format"] = "essentials-actions-v1" }
            if mutation == 4 { actions[0]["prompt"] = (actions[0]["prompt"] as! String).replacingOccurrences(of: "observation at step 30", with: "observation at step 29") }
            if mutation == 5 { actions[0]["observedStep"] = 29 }
            right["actions"] = actions; json["right"] = right
            let bad = try JSONDecoder().decode(ActionComparisonRecord.self, from: JSONSerialization.data(withJSONObject: json))
            XCTAssertThrowsError(try bad.verify(), "mutation \(mutation)")
        }
    }
    func testJournalFreePartnerDoesNotConsumeRequestOrdinal() async throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("request-order-\(UUID())")
        defer { try? FileManager.default.removeItem(at: directory) }
        let spec = ActionComparisonSpecification(stage: .journalOutput, mode: .independentGeneration, steps: 31)
        let run = try await ActionComparisonSession(specification: spec, journalStore: LocalActionJournalStore(directory: directory)).run()
        XCTAssertEqual(run.left?.stage, .sensoryObserver)
        XCTAssertEqual(run.left?.actions.count, 0)
        XCTAssertEqual(run.right.actions.first?.requestOrder, 1)
        try run.verify()
    }
    func testCannotEnableFeedbackMemoryOrFixedRepliesInObservationComparison() throws {
        var s = ActionComparisonSpecification(comparisonKind: .observation)
        XCTAssertThrowsError(try s.validate())
        s.stage = .journalOutput; s.mode = .independentGeneration
        XCTAssertNoThrow(try s.validate())
        s.stage = .journalMemory; XCTAssertThrowsError(try s.validate())
    }
}
private struct FailSensoryBackend: LanguageBackend {
    func reply(to request: LanguageRequest) async throws -> String {
        if !request.prompt.contains("x[0]=") { throw EssentialsError.language("Isolated fixture failure") }
        return ActionRules.envelope(action: .writeJournal, text: "A completed partner observation.")
    }
}
