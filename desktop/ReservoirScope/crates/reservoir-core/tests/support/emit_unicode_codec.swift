// Compiled beside the unchanged TextCodec.swift. Only the unused feedback API
// needs this shape; encode itself is the native source under test.
import Foundation
public struct SpectralMeasurement {
    public var headShare: Double
    public var entropy: Double
    public var shoulderShare: Double
    public var tailShare: Double
}
@main struct UnicodeCodecOracle {
    static func main() throws {
        let request = try JSONSerialization.jsonObject(with: FileHandle.standardInput.readDataToEndOfFile()) as! [String: Any]
        let ranges = request["ranges"] as! [[Int]]
        let clusters = request["clusters"] as! [String]
        let texts = request["texts"] as! [String]
        func flags(_ c: Character) -> Int {
            (c.isLetter ? 1 : 0) | (c.isNumber ? 2 : 0) | (c.isUppercase ? 4 : 0) | (c.isWhitespace ? 8 : 0) | (c.isPunctuation ? 16 : 0)
        }
        var properties: [[Int]] = []
        var lower: [[String]] = []
        for range in ranges {
            for code in range[0]...range[1] {
                guard let scalar = UnicodeScalar(code) else { continue }
                let s = String(scalar)
                let bits = flags(Character(s))
                    | (CharacterSet.whitespaces.contains(scalar) ? 32 : 0)
                    | (CharacterSet.newlines.contains(scalar) ? 64 : 0)
                    | (CharacterSet.whitespacesAndNewlines.contains(scalar) ? 128 : 0)
                if let previous = properties.last, previous[1] + 1 == code && previous[2] == bits {
                    properties[properties.count-1][1] = code
                } else { properties.append([code, code, bits]) }
                if s.lowercased() != s { lower.append([s, s.lowercased()]) }
            }
        }
        let result: [String: Any] = [
            "properties": properties, "lowercase": lower,
            "clusters": clusters.map { ["text": $0, "count": $0.count, "flags": flags(Character($0)), "lowercase": $0.lowercased()] as [String: Any] },
            "vectors": texts.map { ["text": $0, "features": TextCodec.encode($0)] as [String: Any] }
        ]
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]))
    }
}
