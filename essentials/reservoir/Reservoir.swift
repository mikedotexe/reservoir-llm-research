import Foundation

public enum MechanismError: Error, Equatable, Sendable {
    case invalidDimensions
    case nonFiniteValue
    case invalidParameter(String)
    case eigensolverFailed(Int)
}

/// Explicit portable random state; no wall clock, ambient entropy, or global RNG.
public struct SplitMix64: Codable, Sendable {
    public private(set) var state: UInt64
    public init(seed: UInt64) { state = seed }
    public mutating func next() -> UInt64 {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
    public mutating func nextUnit() -> Double { Double(next() >> 11) * 0x1.0p-53 }
    public mutating func nextSigned() -> Double { 2 * nextUnit() - 1 }
    public mutating func symmetric() -> Double { nextSigned() }
}

/// Row-major recurrent weights and input weights, with the final input column a bias.
public struct ReservoirModel: Codable, Sendable, Equatable {
    public let nodeCount: Int
    public let inputCount: Int
    public let recurrentWeights: [Double]
    public let inputWeights: [Double]

    public init(seed: UInt64, nodeCount: Int = 32, inputCount: Int = 66,
                inputScale: Double = 0.5, density: Double = 0.1,
                rowSumBound: Double = 0.9) throws {
        guard (1...4096).contains(nodeCount), (1...4096).contains(inputCount) else {
            throw MechanismError.invalidDimensions
        }
        guard inputScale.isFinite, inputScale >= 0, density.isFinite,
              (0...1).contains(density), rowSumBound.isFinite, rowSumBound >= 0 else {
            throw MechanismError.invalidParameter("weight initialization")
        }
        var rng = SplitMix64(seed: seed)
        var win = [Double](repeating: 0, count: nodeCount * (inputCount + 1))
        for row in 0..<nodeCount {
            for column in 0...inputCount {
                let laneBoost = column < inputCount ? (column >= 18 ? 1.6 : (column >= 16 ? 1.2 : 1)) : 1
                win[row * (inputCount + 1) + column] = rng.nextSigned() * inputScale * laneBoost
            }
        }
        var recurrent = [Double](repeating: 0, count: nodeCount * nodeCount)
        for index in recurrent.indices {
            if rng.nextUnit() < density { recurrent[index] = rng.nextSigned() }
        }
        let maximum = (0..<nodeCount).map { row -> Double in
            let rowWeights = recurrent[(row * nodeCount)..<((row + 1) * nodeCount)]
            return rowWeights.reduce(0.0) { sum, weight in sum + abs(weight) }
        }.max() ?? 0
        if maximum > 0 { recurrent = recurrent.map { $0 * rowSumBound / maximum } }
        try self.init(nodeCount: nodeCount, inputCount: inputCount,
                      recurrentWeights: recurrent, inputWeights: win)
    }

    public init(nodeCount: Int, inputCount: Int, recurrentWeights: [Double], inputWeights: [Double]) throws {
        guard (1...4096).contains(nodeCount), (1...4096).contains(inputCount),
              recurrentWeights.count == nodeCount * nodeCount,
              inputWeights.count == nodeCount * (inputCount + 1) else { throw MechanismError.invalidDimensions }
        guard recurrentWeights.allSatisfy(\.isFinite), inputWeights.allSatisfy(\.isFinite) else {
            throw MechanismError.nonFiniteValue
        }
        self.nodeCount = nodeCount; self.inputCount = inputCount
        self.recurrentWeights = recurrentWeights; self.inputWeights = inputWeights
    }

    private enum CodingKeys: String, CodingKey { case nodeCount, inputCount, recurrentWeights, inputWeights }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        try self.init(nodeCount: values.decode(Int.self, forKey: .nodeCount),
                      inputCount: values.decode(Int.self, forKey: .inputCount),
                      recurrentWeights: values.decode([Double].self, forKey: .recurrentWeights),
                      inputWeights: values.decode([Double].self, forKey: .inputWeights))
    }
}

public struct ReservoirEngine: Sendable {
    public let model: ReservoirModel
    public let leak: Double
    public private(set) var state: [Double]
    public init(model: ReservoirModel, leak: Double = 0.65, state: [Double]? = nil) throws {
        guard leak.isFinite, (0...1).contains(leak) else { throw MechanismError.invalidParameter("leak") }
        let initial = state ?? [Double](repeating: 0, count: model.nodeCount)
        guard initial.count == model.nodeCount else { throw MechanismError.invalidDimensions }
        guard initial.allSatisfy({ $0.isFinite && abs($0) <= 1 }) else { throw MechanismError.nonFiniteValue }
        self.model = model; self.leak = leak; self.state = initial
    }
    /// Noise is an already realized vector. Empty means exactly zero noise.
    @discardableResult
    public mutating func step(input: [Double], noise: [Double] = []) throws -> [Double] {
        guard input.count == model.inputCount, noise.isEmpty || noise.count == model.nodeCount else {
            throw MechanismError.invalidDimensions
        }
        guard input.allSatisfy(\.isFinite), noise.allSatisfy(\.isFinite) else { throw MechanismError.nonFiniteValue }
        var next = [Double](repeating: 0, count: model.nodeCount)
        for row in 0..<model.nodeCount {
            var drive = model.inputWeights[row * (model.inputCount + 1) + model.inputCount]
            for column in input.indices {
                drive += model.inputWeights[row * (model.inputCount + 1) + column] * input[column]
            }
            for column in state.indices { drive += model.recurrentWeights[row * model.nodeCount + column] * state[column] }
            let value = (1 - leak) * state[row] + leak * tanh(drive) + (noise.isEmpty ? 0 : noise[row])
            guard value.isFinite else { throw MechanismError.nonFiniteValue }
            next[row] = min(1, max(-1, value))
        }
        state = next
        return next
    }
}
