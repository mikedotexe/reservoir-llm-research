import Foundation

/// A fresh, small structural/lexical encoder. The last sixteen coordinates
/// deliberately have no embedding, narrative, or reserved-channel content.
public enum TextCodec {
    public static let featureNames = [
        "character entropy", "punctuation density", "uppercase density", "digit density",
        "word length", "character rhythm", "whitespace density", "symbol density",
        "lexical diversity", "hedging markers", "certainty markers", "negation markers",
        "first person", "second person", "action markers", "connectives",
        "sentence length", "sentence length variation", "question density", "exclamation density",
        "ellipsis density", "list lines", "quotation density", "paragraph count",
        "warmth markers", "tension markers", "curiosity markers", "reflection markers",
        "temporal markers", "scale markers", "text length", "feature energy"
    ]

    public static func encode(_ text: String) -> [Double] {
        var f = [Double](repeating: 0, count: 48)
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return f }
        let characters = Array(text)
        let count = Double(max(1, characters.count))
        let words = text.lowercased().split(whereSeparator: { !$0.isLetter && !$0.isNumber && $0 != "'" }).map(String.init)
        let wordCount = Double(max(1, words.count))
        let sentences = text.split(whereSeparator: { ".!?".contains($0) })
        let sentenceCount = Double(max(1, sentences.count))
        let lengths = sentences.map { Double($0.split(whereSeparator: { $0.isWhitespace }).count) }
        let meanLength = lengths.reduce(0, +) / sentenceCount
        let variance = lengths.reduce(0) { $0 + pow($1 - meanLength, 2) } / sentenceCount
        var frequencies: [Character: Int] = [:]
        for c in characters { frequencies[c, default: 0] += 1 }
        let entropy = frequencies.values.reduce(0.0) { value, frequency in
            let p = Double(frequency) / count
            return value - p * log2(p)
        }
        func density(_ predicate: (Character) -> Bool) -> Double { Double(characters.filter(predicate).count) / count }
        func marks(_ set: Set<String>, _ gain: Double = 3) -> Double {
            tanh(gain * Double(words.filter { set.contains($0) }.count) / wordCount)
        }
        func occurrences(_ character: Character) -> Double { Double(characters.filter { $0 == character }.count) }
        f[0] = tanh(entropy)
        f[1] = tanh(1.2 * Double(characters.filter { $0.isPunctuation }.count) / wordCount)
        f[2] = tanh(2 * density { $0.isUppercase })
        f[3] = tanh(3 * density { $0.isNumber })
        f[4] = tanh((words.reduce(0.0) { $0 + Double($1.count) } / wordCount - 4.5) / 2)
        let scalars = text.unicodeScalars.map { Double($0.value) }
        if scalars.count > 1 {
            let movement = zip(scalars, scalars.dropFirst()).reduce(0.0) { $0 + abs($1.0 - $1.1) }
            f[5] = tanh(movement / Double(scalars.count - 1) / 30)
        }
        f[6] = tanh(2 * (density { $0.isWhitespace } - 0.15))
        f[7] = tanh(5 * density { !$0.isLetter && !$0.isNumber && !$0.isWhitespace && !$0.isPunctuation })
        f[8] = tanh(2 * (Double(Set(words).count) / wordCount - 0.5))
        f[9] = marks(["perhaps", "maybe", "might", "could", "seems", "possibly", "uncertain"])
        f[10] = marks(["certain", "clearly", "definitely", "always", "must", "know"], 1.8)
        f[11] = marks(["not", "no", "never", "neither", "without", "cannot", "don't"], 1.2)
        f[12] = marks(["i", "me", "my", "mine", "myself", "we", "our", "us"], 2)
        f[13] = marks(["you", "your", "yours", "yourself"])
        f[14] = marks(["move", "change", "make", "build", "try", "act", "explore", "choose"], 2)
        f[15] = marks(["and", "but", "or", "because", "while", "although", "therefore"])
        f[16] = tanh((wordCount / sentenceCount - 12) / 8)
        f[17] = tanh(sqrt(variance) / 8)
        f[18] = tanh(2 * occurrences("?") / sentenceCount)
        f[19] = tanh(2 * occurrences("!") / sentenceCount)
        f[20] = tanh(Double(max(0, text.components(separatedBy: "...").count - 1)) / sentenceCount)
        let lines = text.components(separatedBy: .newlines)
        f[21] = tanh(Double(lines.filter {
            let line = $0.trimmingCharacters(in: .whitespaces)
            return line.hasPrefix("- ") || line.hasPrefix("* ") || line.hasPrefix("• ")
        }.count) / sentenceCount)
        f[22] = tanh((occurrences("\"") + occurrences("“") + occurrences("”")) / sentenceCount)
        f[23] = tanh(Double(max(0, text.components(separatedBy: "\n\n").filter { !$0.isEmpty }.count - 1)) / 3)
        f[24] = marks(["warm", "care", "love", "gentle", "kind", "together", "thank", "safe"])
        f[25] = marks(["tense", "pressure", "fear", "strain", "tight", "worry", "pain", "difficult"])
        f[26] = marks(["wonder", "curious", "question", "explore", "discover", "why", "how"], 2)
        f[27] = marks(["reflect", "notice", "consider", "understand", "remember", "think", "observe"])
        f[28] = marks(["before", "after", "now", "then", "later", "again", "still", "time"])
        f[29] = marks(["small", "large", "deep", "wide", "little", "much", "more", "less"])
        f[30] = tanh(log(count) / 7)
        f[31] = sqrt(f.prefix(31).reduce(0) { $0 + $1 * $1 } / 31)
        // Fixed semantic gain 2.0. No hidden randomness, word-history, or model calls.
        for index in 0..<32 { f[index] = min(5, max(-5, 2 * f[index])) }
        return f
    }

    /// Reduced forward-spectrum-to-outgoing-codec influence. It operates on
    /// named text coordinates; it never modifies native reservoir node values.
    public static func applySpectralFeedback(_ features: [Double], measurement: SpectralMeasurement) -> [Double] {
        guard features.count == 48, features.allSatisfy(\.isFinite) else { return features }
        var result = features
        let concentration = min(1, max(0, (measurement.headShare - 0.55) / 0.45))
        let lowEntropy = min(1, max(0, (0.45 - measurement.entropy) / 0.45))
        let damping = min(1, max(0, 0.6 * concentration + 0.4 * lowEntropy))
        let lift = min(1, max(0,
            0.45 * min(1, measurement.shoulderShare / 0.35)
            + 0.35 * min(1, measurement.tailShare / 0.30)
            + 0.20 * min(1, max(0, (measurement.entropy - 0.55) / 0.45))))
        result[26] *= 1 - 0.18 * damping
        result[27] *= 1 - 0.14 * damping
        result[31] *= 1 - 0.12 * damping
        result[17] += 0.18 * lift; result[26] += 0.22 * lift
        result[27] += 0.18 * lift; result[31] += 0.16 * lift
        for index in 0..<32 { result[index] = min(5, max(-5, result[index])) }
        for index in 32..<48 { result[index] = 0 }
        return result
    }
}
