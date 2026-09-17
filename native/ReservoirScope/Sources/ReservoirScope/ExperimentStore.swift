import Foundation
import EssentialsCore

/// A copied acceptance app can isolate every preference without changing defaults for ordinary launches.
enum ScopePreferences {
    static var store: UserDefaults { resolve(ProcessInfo.processInfo.environment) }
    static func resolve(_ environment: [String: String]) -> UserDefaults {
        let name = ["RESERVOIR_SCOPE_PREFERENCES", "RESERVOIR_SCOPE_GUIDED_PREFS"]
            .compactMap { environment[$0] }.first { !$0.isEmpty }
        return name.flatMap { UserDefaults(suiteName: $0) } ?? .standard
    }
}

/// Local experiment storage is independent of the build checkout and live feeds.
struct ExperimentStore: Sendable {
    let root: URL
    init(root: URL? = nil) { self.root = root ?? Self.defaultRoot }
    static var defaultRoot: URL {
        if let override = ProcessInfo.processInfo.environment["RESERVOIR_SCOPE_LIBRARY"], override.hasPrefix("/") {
            return URL(fileURLWithPath: override, isDirectory: true)
        }
        return FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Reservoir Scope", isDirectory: true)
    }
    func directory(_ name: String) -> URL { root.appendingPathComponent(name, isDirectory: true) }
    static func requireLocalDestination(_ url: URL) throws {
        guard url.isFileURL, !url.lastPathComponent.isEmpty else {
            throw EssentialsError.invalid("Choose a local file for the exported experiment.")
        }
    }
    struct Entry: Identifiable, Sendable {
        let id: String
        let title: String
        let detail: String
        let format: String
        let url: URL
        let bundled: Bool
        var group: String = "saved"
        var order: Int = 0
        var lessonID: String? = nil
    }
    private struct Metadata: Decodable {
        let format: String?
        let recipeVersion: String?
        let seed: UInt64?
        let status: String?
        let specification: Specification?
        struct Specification: Decodable {
            let stage: Int?
            let seed: UInt64?
            let comparisonKind: String?
            let language: Language?
        }
        struct Language: Decodable { let backend: String; let model: String? }
    }
    static func inspect(_ url: URL) throws -> (format: String, title: String, detail: String) {
        let values = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
        guard values.isRegularFile == true, (values.fileSize ?? Int.max) <= 256 * 1024 * 1024 else {
            throw EssentialsError.invalid("Experiment must be a regular JSON file no larger than 256 MB.")
        }
        let data = try Data(contentsOf: url)
        guard data.count <= 256 * 1024 * 1024 else { throw EssentialsError.invalid("Experiment exceeds the file limit.") }
        let m = try JSONDecoder().decode(Metadata.self, from: data)
        let title: String
        let format = m.format ?? m.recipeVersion ?? ""
        switch format {
        case "essentials-actions-v1", "essentials-actions-v2", "essentials-actions-v3":
            title = m.specification?.comparisonKind == "observation" ? "What can the journal observe?" : ActionStage(rawValue: m.specification?.stage ?? 0)?.title ?? "Actions comparison"
        case "essentials-regulation-v1": title = "Controller mechanism example"
        case "essentials-exploration-v1": title = "Reservoir exploration"
        case "essentials-v1": title = "Stage experiment \(m.specification?.stage ?? 0)"
        default: throw EssentialsError.invalid("Unrecognized experiment format.")
        }
        let model = m.specification?.language
        let origin = model?.backend == "ollama" ? "Recorded model run · \(model?.model ?? "model unavailable")" : "Scripted example / recorded simulation"
        let seed = m.specification?.seed ?? m.seed
        let detail = origin + (seed.map { " · seed \($0)" } ?? "") + (m.status.map { " · " + $0 } ?? "")
        return (format, title, detail)
    }
    func entries() throws -> [Entry] {
        guard FileManager.default.fileExists(atPath: root.path) else { return [] }
        guard let files = FileManager.default.enumerator(at: root, includingPropertiesForKeys: [.isRegularFileKey], options: [.skipsHiddenFiles]) else { return [] }
        var result: [Entry] = []
        var dates: [String: Date] = [:]
        var examined = 0
        for case let url as URL in files {
            examined += 1
            if examined > 5000 || result.count >= 500 { break }
            guard url.pathExtension == "json" else { continue }
            if let m = try? Self.inspect(url) {
                let date = (try? url.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                dates[url.path] = date
                result.append(Entry(id: url.path, title: m.title, detail: m.detail + " · " + DateFormatter.localizedString(from: date, dateStyle: .medium, timeStyle: .short),
                                    format: m.format, url: url, bundled: false))
            }
        }
        return result.sorted { (dates[$0.id] ?? .distantPast) > (dates[$1.id] ?? .distantPast) }
    }
    func importVerified(_ url: URL) throws -> URL {
        let m = try Self.inspect(url)
        // Copy once, then verify that exact local snapshot. Imported paths remain data.
        let folder = directory("Imports")
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let target = folder.appendingPathComponent("import-\(UUID().uuidString).json")
        try FileManager.default.copyItem(at: url, to: target)
        do {
            switch m.format {
            case "essentials-actions-v1", "essentials-actions-v2", "essentials-actions-v3": _ = try ActionComparisonRecord.read(from: target).verify()
            case "essentials-regulation-v1": _ = try RegulationExampleRecord.read(from: target).verify()
            case "essentials-exploration-v1": _ = try ExplorationRecord.read(from: target).verify()
            default: _ = try RunVerifier.verify(RunRecord.read(from: target))
            }
        } catch { try? FileManager.default.removeItem(at: target); throw error }
        return target
    }
}
