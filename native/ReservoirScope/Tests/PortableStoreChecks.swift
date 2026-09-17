import Foundation
import EssentialsCore

struct SurfaceRenderError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}
@MainActor private final class PortableClock { var time = 0.0 }

@MainActor private func portableChecks() async throws {
    guard CommandLine.arguments.count == 3 else { throw SurfaceRenderError("Expected packaged resources and a new export directory") }
    let resources = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
    let exports = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
    try FileManager.default.createDirectory(at: exports, withIntermediateDirectories: true)
    func require(_ condition: Bool, _ message: String) throws {
        guard condition else { throw SurfaceRenderError(message) }
        print("PASS: " + message)
    }
    func idle(_ model: ActionComparisonViewModel) async throws {
        for _ in 0..<3000 {
            if !model.working && !model.loading { return }
            try await Task.sleep(for: .milliseconds(5))
        }
        throw SurfaceRenderError("Native operation timed out")
    }
    for stage in ActionStage.allCases {
        let clock = PortableClock(), model = ActionComparisonViewModel(uptime: { clock.time })
        model.select(stage); model.run(); try await idle(model)
        let protocols = (FileManager.default.enumerator(at: ExperimentStore().directory("Actions"), includingPropertiesForKeys: nil)?.allObjects as? [URL] ?? []).filter { $0.lastPathComponent == "protocol.json" }
        try require(protocols.count == stage.rawValue && model.framesCount == 0, "Protocol is saved before the first observation or generation")
        for _ in 0..<31 { clock.time += 1; model.tick(); try await idle(model) }
        model.stop()
        try require(await model.flushForTermination(), "Stage \(stage.rawValue) local save completed before quit")
        guard let record = model.record else { throw SurfaceRenderError("Missing stage record") }
        try require(record.stepCount == 31 && record.specification.steps == 300, "Stage \(stage.rawValue) preserves the interactive default")
        try require(record.right.journals.count == (stage.hasJournal ? 1 : 0), "Stage \(stage.rawValue) journal availability matches its component")
        let output = exports.appendingPathComponent("stage-\(stage.rawValue).json")
        try record.write(to: output)
        let imported = try ExperimentStore().importVerified(output)
        let reopened = ActionComparisonViewModel()
        reopened.open(imported); try await idle(reopened)
        try require(reopened.row == 0 && reopened.rightAction == nil && reopened.record?.stepCount == 31,
                    "Stage \(stage.rawValue) reopens at the first cursor without future journal text")
        reopened.nextJournal()
        if stage.hasJournal { try require(reopened.row == 29 && reopened.rightAction?.observedStep == 30, "Recorded Next journal moves the cursor without generation") }
        if stage == .reservoirReturn {
            let before = try ExperimentStore().entries().count
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            let originalBytes = try encoder.encode(reopened.record)
            try require(reopened.applicationStepAtCursor(reopened.rightAction!) == nil,
                        "Loaded E hides the future feedback application while its cursor is at step 30")
            reopened.step(); try await idle(reopened)
            try require(reopened.row == 30 && reopened.rightFrame?.step == 31
                        && reopened.applicationStepAtCursor(reopened.rightAction!) == 31,
                        "Loaded E Step advances the recorded cursor from 30 to feedback at 31")
            try require(try encoder.encode(reopened.record) == originalBytes,
                        "Stepping loaded E preserves the complete record, prompts and journals")
            try require(await reopened.flushForTermination(), "Loaded E replay closes without a new experiment")
            try require(try ExperimentStore().entries().count == before,
                        "Loaded E Step and quit do not add any saved run or journal entry")
        }
        try require(await reopened.flushForTermination(), "Reopened record remains locally recoverable")
    }
    let exploration = ExplorationViewModel()
    exploration.step(); exploration.step()
    try require(await exploration.flushForTermination(), "Explore saves in the shared local store")
    let original = resources.appendingPathComponent("essentials-stage-3.json")
    let stageImport = try ExperimentStore().importVerified(original)
    try require(try ExperimentStore.inspect(stageImport).format == "essentials-v1", "Original stage records remain importable")
    let legacy = try ExperimentStore().importVerified(resources.appendingPathComponent("essentials-actions-feedback.json"))
    try require(try ActionComparisonRecord.read(from: legacy).format == ActionComparisonRecord.legacyFormat, "Legacy action records retain the v1 verification path")
    let v2 = try ExperimentStore().importVerified(resources.appendingPathComponent("example-component-5.json"))
    let v2Record = try ActionComparisonRecord.read(from: v2)
    try require(v2Record.format == ActionComparisonRecord.previousFormat && v2Record.specification.forcingProfile == .pulsedSensoryV1,
                "Existing v2 examples remain importable with their original pulsed-input interpretation")
    try require(try v2Record.verify().checkedSteps == 240, "Imported v2 keeps its exact prompt and numerical verification path")

    // Copy into another local library and remove the chosen source. Verification
    // uses the embedded record, not a source path or adjacent journal files.
    let otherStore = ExperimentStore(root: exports.appendingPathComponent("another-local-library", isDirectory: true))
    let sourceDirectory = exports.appendingPathComponent("temporary-originals", isDirectory: true)
    try FileManager.default.createDirectory(at: sourceDirectory, withIntermediateDirectories: true)
    let activeSource = sourceDirectory.appendingPathComponent("active-observation.json")
    try FileManager.default.copyItem(at: resources.appendingPathComponent("example-observation-active-scripted.json"), to: activeSource)
    let activeImport = try otherStore.importVerified(activeSource)
    try FileManager.default.removeItem(at: activeSource)
    let active = try ActionComparisonRecord.read(from: activeImport)
    try require(active.format == ActionComparisonRecord.currentFormat && active.specification.forcingProfile == .continuousSensoryV1,
                "Shared store imports v3 with its explicit continuous observation profile")
    try require(try active.verify().checkedSteps == 240
                && active.left?.frames.map(\.state) == active.right.frames.map(\.state),
                "Relocated v3 verifies identical arm trajectories after its original file is removed")
    let missingJournalFiles = active.right.actions.compactMap { $0.saveReceipt?.relativePath }.allSatisfy {
        !FileManager.default.fileExists(atPath: activeImport.deletingLastPathComponent().appendingPathComponent($0).path)
    }
    try require(missingJournalFiles && active.right.journals.count == 3,
                "Portable journals replay from embedded text without following historical relative save paths")
    let relocatedModel = ActionComparisonViewModel()
    relocatedModel.open(activeImport); try await idle(relocatedModel)
    relocatedModel.nextJournal()
    try require(relocatedModel.rightAction?.observedStep == 30 && relocatedModel.record?.specification.forcingProfile == .continuousSensoryV1,
                "Native replay opens relocated v3 and exposes its recorded opportunity")
    try require(await relocatedModel.flushForTermination(), "Relocated v3 replay does not require its original source")

    let controllerSource = sourceDirectory.appendingPathComponent("controller.json")
    try FileManager.default.copyItem(at: resources.appendingPathComponent("example-regulation-controller.json"), to: controllerSource)
    let controllerImport = try otherStore.importVerified(controllerSource)
    try FileManager.default.removeItem(at: sourceDirectory)
    let controller = try RegulationExampleRecord.read(from: controllerImport)
    try require(try controller.verify().checkedSteps == 1200 && controller.frames.count == 600,
                "Shared store preserves and verifies all paired controller observations without the original directory")
    try require(controller.summary.evaluationCount == 300
                && controller.summary.regulatedMeanAbsoluteError < controller.summary.baselineMeanAbsoluteError,
                "Imported controller evidence preserves its declared evaluation window and measured result")
    let controllerExport = exports.appendingPathComponent("controller-export.json")
    try controller.write(to: controllerExport)
    let sharedController = try ExperimentStore().importVerified(controllerExport)
    try require(try RegulationExampleRecord.read(from: sharedController).verify().checkedSteps == 1200,
                "Controller export reopens through the same shared-store verification route")

    let entriesBeforeRejectedImport = Set(try otherStore.entries().map(\.id))
    var badController = try JSONSerialization.jsonObject(with: Data(contentsOf: controllerExport)) as! [String: Any]
    var badSummary = badController["summary"] as! [String: Any]
    badSummary["regulatedMeanAbsoluteError"] = 0
    badController["summary"] = badSummary
    let badControllerURL = exports.appendingPathComponent("tampered-controller.json")
    try JSONSerialization.data(withJSONObject: badController).write(to: badControllerURL)
    var rejectedController = false
    do { _ = try otherStore.importVerified(badControllerURL) } catch { rejectedController = true }
    try require(rejectedController && Set(try otherStore.entries().map(\.id)) == entriesBeforeRejectedImport,
                "A changed controller result is rejected and its failed import leaves no library entry")
    try FileManager.default.removeItem(at: badControllerURL)

    var badAction = try JSONSerialization.jsonObject(with: Data(contentsOf: activeImport)) as! [String: Any]
    badAction["format"] = ActionComparisonRecord.previousFormat
    let badActionURL = exports.appendingPathComponent("tampered-v2-profile.json")
    try JSONSerialization.data(withJSONObject: badAction).write(to: badActionURL)
    var rejectedProfile = false
    do { _ = try otherStore.importVerified(badActionURL) } catch { rejectedProfile = true }
    try require(rejectedProfile && Set(try otherStore.entries().map(\.id)) == entriesBeforeRejectedImport,
                "Shared-store import rejects continuous-input evidence mislabeled as legacy v2")
    try FileManager.default.removeItem(at: badActionURL)
    let namedExport = ExperimentStore.defaultRoot.appendingPathComponent("my-chosen-export.json")
    try FileManager.default.copyItem(at: legacy, to: namedExport)
    let entries = try ExperimentStore().entries()
    try require(entries.contains { $0.url.resolvingSymlinksInPath() == namedExport.resolvingSymlinksInPath() }, "Runs browser recognizes a user-named export in the local store")
    try require(entries.contains { $0.format == "essentials-exploration-v1" } && entries.contains { $0.format == "essentials-v1" }
                && entries.contains { $0.format == ActionComparisonRecord.currentFormat }
                && entries.contains { $0.format == ActionComparisonRecord.previousFormat }
                && entries.contains { $0.format == RegulationExampleRecord.currentFormat }, "Runs browser discovers current, legacy and controller experiment formats")
    let report: [String: Any] = ["status":"passed", "stages":8, "steps_per_native_stage":31,
        "shared_store":ExperimentStore.defaultRoot.path, "export_directory":exports.path, "entries":entries.count,
        "legacy_action_formats":[ActionComparisonRecord.legacyFormat, ActionComparisonRecord.previousFormat],
        "new_action_format":ActionComparisonRecord.currentFormat, "controller_format":RegulationExampleRecord.currentFormat,
        "loaded_E_feedback_step":31, "controller_steps_per_arm":600, "rejected_imports":2,
        "scope":"Production native view models and filesystem store, new view-model instances on replay; no backend or live feed enabled."]
    try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted,.sortedKeys]).write(to: exports.appendingPathComponent("native-store-receipt.json"))
}
Task { @MainActor in
    do { try await portableChecks(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
