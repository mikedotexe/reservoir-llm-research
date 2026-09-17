import Foundation
import CryptoKit

struct ResearchCaseError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

struct ReviewedResearchCase: Codable, Identifiable, Sendable {
    let id: String
    let title: String
    let question: String
    let summary: String
    let author: String
    let sourceOwner: String
    let interval: String
    let limits: [String]
    let materials: [Material]
    let claims: [Claim]
    let sequence: [Event]

    struct Material: Codable, Identifiable, Sendable {
        let id: String
        let title: String
        let kind: String
        let content: String
        let sha256: String
        let sourcePath: String?
        let sourceSHA256: String?
        let note: String?
    }
    enum Classification: String, Codable, Sendable {
        case supported, contradicted, unresolved, recalled
        var title: String {
            switch self {
            case .supported: return "Supported by the cited evidence"
            case .contradicted: return "Contradicted by the cited evidence"
            case .unresolved: return "Unresolved"
            case .recalled: return "Recalled account"
            }
        }
    }
    struct Claim: Codable, Identifiable, Sendable {
        let id: String
        let classification: Classification
        let materialID: String
        let quote: String
        let evidenceIDs: [String]
        let explanation: String
    }
    struct Event: Codable, Sendable {
        enum Status: String, Codable, Sendable { case observed, notObserved }
        let title: String
        let detail: String
        let materialIDs: [String]
        let status: Status
        let timestamp: String?
    }
    func material(_ id: String) -> Material? { materials.first { $0.id == id } }
}

struct ResearchCaseCatalog: Codable, Sendable {
    static let currentFormat = "research-cases-v1"
    static let maximumBytes = 32 * 1024 * 1024
    let format: String
    let cases: [ReviewedResearchCase]
    init(cases: [ReviewedResearchCase]) { self.format = Self.currentFormat; self.cases = cases }

    static func digest(_ content: String) -> String {
        SHA256.hash(data: Data(content.utf8)).map { String(format: "%02x", $0) }.joined()
    }
    static func read(from url: URL) throws -> Self {
        try decode(readData(from: url, limit: maximumBytes))
    }
    /// Recognize case imports without reducing the existing numerical import size limit.
    /// Original paths inside a case are never read.
    static func readIfSupported(from url: URL) throws -> Self? {
        let data = try readData(from: url, limit: 256 * 1024 * 1024)
        struct Header: Decodable { let format: String? }
        guard let header = try? JSONDecoder().decode(Header.self, from: data),
              header.format == currentFormat else { return nil }
        return try decode(data)
    }
    private static func readData(from url: URL, limit: Int) throws -> Data {
        guard url.isFileURL else { throw ResearchCaseError("Choose a local research case file.") }
        let values = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
        guard values.isRegularFile == true, let size = values.fileSize, size <= limit else {
            throw ResearchCaseError("The research case file is not a regular file or exceeds the size limit.")
        }
        let data = try Data(contentsOf: url, options: .mappedIfSafe)
        guard data.count <= limit else { throw ResearchCaseError("The research case file exceeds the size limit.") }
        return data
    }
    static func decode(_ data: Data) throws -> Self {
        guard data.count <= maximumBytes else { throw ResearchCaseError("Research cases must be no larger than 32 MiB.") }
        let catalog = try JSONDecoder().decode(Self.self, from: data)
        try catalog.verify()
        return catalog
    }
    func encoded() throws -> Data {
        try verify()
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        let data = try encoder.encode(self)
        guard data.count <= Self.maximumBytes else { throw ResearchCaseError("Research cases must be no larger than 32 MiB.") }
        return data
    }
    func verify() throws {
        func require(_ condition: Bool, _ message: String) throws {
            guard condition else { throw ResearchCaseError(message) }
        }
        func nonempty(_ text: String) -> Bool { !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        func isDigest(_ text: String) -> Bool {
            text.count == 64 && text.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
        }
        try require(format == Self.currentFormat, "Unsupported research case format.")
        try require(!cases.isEmpty && cases.count <= 20, "A case catalog must contain between one and twenty cases.")
        try require(Set(cases.map(\.id)).count == cases.count, "Research case IDs must be unique.")
        for item in cases {
            try require([item.id, item.title, item.question, item.summary, item.author, item.sourceOwner, item.interval].allSatisfy(nonempty),
                        "A research case is missing its question, ownership, interval, or description.")
            try require(!item.limits.isEmpty && item.limits.allSatisfy(nonempty), "Every research case must state its limits.")
            try require(!item.materials.isEmpty && item.materials.count <= 100, "Every case needs bounded embedded evidence.")
            try require(Set(item.materials.map(\.id)).count == item.materials.count, "Material IDs must be unique within a case.")
            let ids = Set(item.materials.map(\.id))
            for material in item.materials {
                try require([material.id, material.title, material.kind, material.content].allSatisfy(nonempty), "An embedded material is empty.")
                try require(isDigest(material.sha256) && Self.digest(material.content) == material.sha256,
                            "Embedded evidence hash does not match: " + material.title)
                if let original = material.sourceSHA256 {
                    try require(isDigest(original), "An original-source hash is malformed.")
                }
            }
            try require(!item.claims.isEmpty && item.claims.count <= 100, "A reviewed case needs a bounded claim reading.")
            try require(Set(item.claims.map(\.id)).count == item.claims.count, "Claim IDs must be unique within a case.")
            for claim in item.claims {
                try require([claim.id, claim.quote, claim.explanation].allSatisfy(nonempty), "A reviewed claim is incomplete.")
                guard let material = item.material(claim.materialID) else { throw ResearchCaseError("A claim refers to absent material.") }
                try require(material.content.components(separatedBy: claim.quote).count - 1 == 1,
                            "A claim quote must occur exactly once in its embedded material: " + claim.id)
                try require(!claim.evidenceIDs.isEmpty && claim.evidenceIDs.allSatisfy(ids.contains), "A claim's cited evidence is absent.")
            }
            try require(!item.sequence.isEmpty && item.sequence.count <= 100, "A reviewed case needs its observed sequence and limits.")
            for event in item.sequence {
                try require(nonempty(event.title) && nonempty(event.detail), "A sequence entry is incomplete.")
                try require(event.materialIDs.allSatisfy(ids.contains), "A sequence entry refers to absent material.")
                if event.status == .observed {
                    try require(!event.materialIDs.isEmpty, "Observed sequence entries need embedded evidence.")
                }
            }
        }
    }
}
