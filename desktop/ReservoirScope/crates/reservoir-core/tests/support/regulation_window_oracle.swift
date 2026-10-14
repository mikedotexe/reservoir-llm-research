// Compile alongside the actual native GuidedLessons.swift and EssentialsCore.
// The wrapper only serializes its RegulationWindowEvidence result.
import Foundation
import EssentialsCore

struct Window: Encodable {
    let count: Int
    let firstStep: Int
    let lastStep: Int
    let isComplete: Bool
    let baselineMeanAbsoluteError: Double
    let regulatedMeanAbsoluteError: Double
    init(_ v: RegulationWindowEvidence) {
        count = v.count; firstStep = v.firstStep; lastStep = v.lastStep
        isComplete = v.isComplete
        baselineMeanAbsoluteError = v.baselineMeanAbsoluteError
        regulatedMeanAbsoluteError = v.regulatedMeanAbsoluteError
    }
}
struct ResultRow: Encodable {
    let cursor: Int
    let evidence: Window?
    enum CodingKeys: String, CodingKey { case cursor, evidence }
    func encode(to encoder: Encoder) throws {
        var c=encoder.container(keyedBy: CodingKeys.self)
        try c.encode(cursor,forKey:.cursor)
        if let evidence { try c.encode(evidence,forKey:.evidence) }
        else { try c.encodeNil(forKey:.evidence) }
    }
}
@main struct RegulationWindowOracle {
    static func main() throws {
        guard CommandLine.arguments.count == 2 else { throw NSError(domain:"usage",code:1) }
        let record=try RegulationExampleRecord.read(from:URL(fileURLWithPath:CommandLine.arguments[1]))
        _ = try record.verify()
        let rows=[0,300,301,450,599,600,450,301,300,900].map { cursor in
            ResultRow(cursor:cursor,evidence:RegulationWindowEvidence.evaluate(record,cursorStep:cursor).map(Window.init))
        }
        let encoder=JSONEncoder(); encoder.outputFormatting=[.sortedKeys]
        FileHandle.standardOutput.write(try encoder.encode(rows))
    }
}
