import Foundation

/// Named, immutable synthetic input recipes. Their versions are part of replay evidence.
public enum ActionForcingProfile: String, Codable, CaseIterable, Sendable {
    case pulsedSensoryV1
    case continuousSensoryV1

    public var title: String {
        self == .pulsedSensoryV1 ? "Pulsed sensory input" : "Continuous sensory input"
    }

    /// Both profiles use the same sixteen sinusoidal sensory coordinates. The
    /// continuous example removes only the twelve-on/eighteen-off envelope.
    /// Auxiliary and journal-return coordinates are zero here.
    public func input(step: Int, dt: Double = 1.0 / 3.0) -> [Double] {
        Recipe.forcing(step: step, dt: dt, continuous: self == .continuousSensoryV1)
    }
}
