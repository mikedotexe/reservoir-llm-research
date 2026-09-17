import AppKit

/// Quit waits for local record writes. Failed writes leave the app open unless
/// the researcher explicitly discards the retained in-memory evidence.
@MainActor final class ExperimentLifecycle {
    static let shared = ExperimentLifecycle()
    var prepare: (() async -> Bool)?
}

@MainActor final class ScopeApplicationDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard let prepare = ExperimentLifecycle.shared.prepare else { return .terminateNow }
        Task { @MainActor in
            let saved = await prepare()
            if saved { sender.reply(toApplicationShouldTerminate: true); return }
            let alert = NSAlert()
            alert.messageText = "Some experiments are still only in memory"
            alert.informativeText = "Return to the app to retry saving or export the retained records. Quitting now will discard those unsaved records."
            alert.addButton(withTitle: "Return to app")
            alert.addButton(withTitle: "Discard and quit")
            sender.reply(toApplicationShouldTerminate: alert.runModal() == .alertSecondButtonReturn)
        }
        return .terminateLater
    }
}
