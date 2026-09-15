import Foundation

/// Reduced normalized rank measure over ALL supplied field eigenvalues, not native RMS.
public struct ReducedFill: Codable, Sendable {
    public private(set) var fill: Double = 0
    public init() {}
    @discardableResult
    public mutating func update(eigenvalues: [Double], dt: Double = 1.0 / 3.0) -> Double {
        guard dt.isFinite, dt >= 0, !eigenvalues.isEmpty, eigenvalues.allSatisfy(\.isFinite) else { return fill }
        let values = eigenvalues.map { max(0, $0) }
        let mean = values.reduce(0, +) / Double(values.count)
        let active = mean > 1e-12 ? values.filter { $0 > 0.12 * mean }.count : 0
        let instant = active > 0 ? max(0.04, Double(active) / Double(values.count)) : 0
        fill = min(1, max(0, 0.10 * instant + 0.90 * (1 - min(0.15, 0.006 * dt)) * fill))
        return fill
    }
}

public struct ControlMeasurement: Codable, Sendable, Equatable {
    /// Signed percentage-point error before deadband.
    public let error: Double
    public let integral: Double
    public let requestedRetention: Double
    /// This value controls the NEXT field update.
    public let appliedRetention: Double
}

public struct RetentionController: Codable, Sendable {
    public private(set) var currentRetention: Double = 0.955
    public private(set) var integral: Double = 0
    public var targetFillPct: Double { 68 }
    public init() {}
    public init(initialRetention: Double) throws {
        guard initialRetention.isFinite, (0.82...0.995).contains(initialRetention) else {
            throw MechanismError.invalidParameter("initial retention")
        }
        currentRetention = initialRetention
    }
    @discardableResult
    public mutating func update(fillPct: Double) -> ControlMeasurement {
        guard fillPct.isFinite else {
            return ControlMeasurement(error: 0, integral: integral, requestedRetention: currentRetention, appliedRetention: currentRetention)
        }
        let error = fillPct - targetFillPct
        let e = (error < 0 ? -1.0 : 1.0) * max(0, abs(error) - 4) / 20
        let tentative = min(1, max(-1, 0.85 * integral + e))
        let u = min(0.12, max(-0.12, 0.55 * e + 0.04 * tentative))
        let requested = min(0.995, max(0.82, 0.955 - u))
        if (requested <= 0.82 && e > 0) || (requested >= 0.995 && e < 0) { integral *= 0.85 }
        else { integral = tentative }
        currentRetention += min(0.01, max(-0.01, requested - currentRetention))
        return ControlMeasurement(error: error, integral: integral, requestedRetention: requested, appliedRetention: currentRetention)
    }
}
