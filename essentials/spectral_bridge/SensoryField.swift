import Foundation
import Accelerate

public struct SpectralMeasurement: Codable, Sendable, Equatable {
    public let dimension: Int
    public let eigenvalues: [Double]
    /// Mode-major vectors: one full field vector for each descending eigenvalue.
    public let eigenvectors: [Double]
    public let fieldVector: [Double]
    public let covariance: [Double]
    /// These summary quantities describe the displayed first eight modes only.
    public let entropy: Double
    public let headShare: Double
    public let shoulderShare: Double
    public let tailShare: Double
    public var displayEigenvalues: [Double] { Array(eigenvalues.prefix(8)) }
}

public struct SensoryField: Sendable {
    public let dimension: Int
    public let inputCount: Int
    public let projection: [Double]
    public var projectionWeights: [Double] { projection }
    public private(set) var covariance: [Double]

    public init(seed: UInt64, dimension: Int = 32, inputCount: Int = 66) throws {
        guard (1...4096).contains(dimension), (1...4096).contains(inputCount) else { throw MechanismError.invalidDimensions }
        var rng = SplitMix64(seed: seed)
        let weights = (0..<(dimension * inputCount)).map { _ in rng.nextSigned() }
        try self.init(dimension: dimension, inputCount: inputCount, projection: weights)
    }

    public init(dimension: Int, inputCount: Int, projection: [Double], covariance: [Double]? = nil) throws {
        guard (1...4096).contains(dimension), (1...4096).contains(inputCount),
              projection.count == dimension * inputCount else { throw MechanismError.invalidDimensions }
        guard projection.allSatisfy(\.isFinite) else { throw MechanismError.nonFiniteValue }
        var matrix = covariance ?? [Double](repeating: 0, count: dimension * dimension)
        if covariance == nil { for i in 0..<dimension { matrix[i * dimension + i] = 1 } }
        guard matrix.count == dimension * dimension else { throw MechanismError.invalidDimensions }
        guard matrix.allSatisfy(\.isFinite) else { throw MechanismError.nonFiniteValue }
        for i in 0..<dimension { for j in 0..<i {
            guard abs(matrix[i * dimension + j] - matrix[j * dimension + i]) <= 1e-10 else {
                throw MechanismError.invalidParameter("covariance symmetry")
            }
        } }
        self.dimension = dimension; self.inputCount = inputCount
        self.projection = projection; self.covariance = matrix
    }

    public mutating func step(input: [Double], retention: Double = 0.955) throws -> SpectralMeasurement {
        guard input.count == inputCount else { throw MechanismError.invalidDimensions }
        guard input.allSatisfy(\.isFinite) else { throw MechanismError.nonFiniteValue }
        guard retention.isFinite, (0...0.9999).contains(retention) else { throw MechanismError.invalidParameter("retention") }
        let activated = input.enumerated().map { index, value -> Double in
            let scale = index < 8 ? 0.75 : (index < 16 ? 0.72 : (index < 18 ? 1.12 : 0.42))
            return tanh(value * scale * 0.58)
        }
        var z = [Double](repeating: 0, count: dimension)
        for row in 0..<dimension {
            for column in 0..<inputCount { z[row] += projection[row * inputCount + column] * activated[column] }
            z[row] /= sqrt(Double(inputCount))
        }
        let rms = sqrt(z.reduce(0) { $0 + $1 * $1 } / Double(dimension))
        if rms > 1e-12 { z = z.map { $0 / rms } }
        else { z = [Double](repeating: 0, count: dimension) }
        var next = covariance
        for row in 0..<dimension { for column in 0..<dimension {
            next[row * dimension + column] = retention * covariance[row * dimension + column]
                + (1 - retention) * z[row] * z[column]
        } }
        // Silence decays actual covariance energy; never normalize it back into existence.
        let trace = (0..<dimension).reduce(0.0) { $0 + next[$1 * dimension + $1] }
        if rms > 1e-12, trace > 1e-12 {
            let scale = min(2, Double(dimension) / trace)
            next = next.map { $0 * scale }
        }
        let eigensystem = try Self.eigensystem(matrix: next, dimension: dimension)
        covariance = next
        let summary = Self.summary(eigenvalues: eigensystem.values)
        return SpectralMeasurement(dimension: dimension, eigenvalues: eigensystem.values,
                                   eigenvectors: eigensystem.vectors, fieldVector: z, covariance: next,
                                   entropy: summary.entropy, headShare: summary.head,
                                   shoulderShare: summary.shoulder, tailShare: summary.tail)
    }

    public static func summary(eigenvalues: [Double]) -> (entropy: Double, head: Double, shoulder: Double, tail: Double) {
        let values = eigenvalues.prefix(8).map { $0.isFinite ? max(0, $0) : 0 }
        let total = values.reduce(0, +)
        guard total > 1e-12 else { return (0, 0, 0, 0) }
        let shares = values.map { $0 / total }
        let entropy = shares.reduce(0.0) { $0 + ($1 > 0 ? -$1 * log($1) : 0) }
        return (shares.count > 1 ? entropy / log(Double(shares.count)) : 0,
                shares.first ?? 0, shares.dropFirst().prefix(2).reduce(0, +), shares.dropFirst(3).reduce(0, +))
    }

    /// Standard LAPACK eigendecomposition; it does not encode any reservoir dynamics.
    public static func eigensystem(matrix: [Double], dimension: Int) throws -> (values: [Double], vectors: [Double]) {
        guard dimension > 0, matrix.count == dimension * dimension else { throw MechanismError.invalidDimensions }
        guard matrix.allSatisfy(\.isFinite) else { throw MechanismError.nonFiniteValue }
        var a = matrix
        var n = __CLPK_integer(dimension), lda = __CLPK_integer(dimension)
        var values = [Double](repeating: 0, count: dimension)
        var job: Int8 = 86, upper: Int8 = 85, info: __CLPK_integer = 0
        var length: __CLPK_integer = -1
        var query = [Double](repeating: 0, count: 1)
        dsyev_(&job, &upper, &n, &a, &lda, &values, &query, &length, &info)
        guard info == 0 else { throw MechanismError.eigensolverFailed(Int(info)) }
        length = __CLPK_integer(max(1, Int(query[0])))
        var work = [Double](repeating: 0, count: Int(length))
        dsyev_(&job, &upper, &n, &a, &lda, &values, &work, &length, &info)
        guard info == 0 else { throw MechanismError.eigensolverFailed(Int(info)) }
        var vectors: [Double] = []
        for column in (0..<dimension).reversed() {
            var vector = Array(a[(column * dimension)..<((column + 1) * dimension)])
            // Fix each mode's sign for presentation; degenerate bases remain unspecified.
            if let largest = vector.indices.max(by: { abs(vector[$0]) < abs(vector[$1]) }), vector[largest] < 0 {
                vector = vector.map { -$0 }
            }
            vectors.append(contentsOf: vector)
        }
        return (values.reversed().map { max(0, $0) }, vectors)
    }
}
