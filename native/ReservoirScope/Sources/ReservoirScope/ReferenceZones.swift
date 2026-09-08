import Foundation

/// Explanatory references for the inspected stable-core source, not reconstructed
/// controller states. Positions come from the loaded evidence's configuration.
struct ReferenceZone: Identifiable, Sendable {
    enum Kind: String, Sendable {
        case shelfBoundary = "Shelf boundary"
        case transition = "State transition"
        case target = "Reference target"
        case piThreshold = "PI allowance"
        case strongRail = "Strong drain"
        case warningRail = "Warning rail"
    }

    enum StyleRole: String, Sendable {
        case shelf, hysteresis, target, pi, strong, force
    }

    enum Comparison: String, Sendable {
        case atOrBelow = "≤"
        case atOrAbove = "≥"
        case strictlyAbove = ">"
        case reference = "Reference"
    }

    let id: String
    let title: String
    let thresholdPct: Double
    let relatedThresholdPct: Double?
    let kind: Kind
    let comparison: Comparison
    let summary: String
    let detail: String
    /// Relative to the Minime repository, matching data.json's source contract.
    let sourceRelativePath: String
    let sourceLine: Int
    let styleRole: StyleRole

    var thresholdLabel: String { Self.percent(thresholdPct) }
    var sourceLabel: String { "\(sourceRelativePath):\(sourceLine)" }

    /// A scalar comparison only. Stage history and controller availability are
    /// deliberately not inferred from this relation.
    func matchesThreshold(_ fillPct: Double) -> Bool {
        guard fillPct.isFinite else { return false }
        switch comparison {
        case .atOrBelow: return fillPct <= thresholdPct
        case .atOrAbove: return fillPct >= thresholdPct
        case .strictlyAbove: return fillPct > thresholdPct
        case .reference: return fillPct == thresholdPct
        }
    }

    static let evidenceScope = "Source-defined operating references. Historical controller stage and mode were not recorded with this replay. The shelf is an intended operating range, not measured subjective comfort or a guarantee of stability."

    static func catalog(bands: ReferenceBands, configuration: StructuralPIConfiguration) -> [ReferenceZone] {
        let overfill = "minime/src/rescue_overfill.rs"
        let scaffold = "minime/src/rescue_scaffold.rs"
        let piOnset = configuration.targetFillPct + configuration.deadbandPct
        var zones = [ReferenceZone(
            id: "shelf-release", title: "Hold releases", thresholdPct: bands.shelfMinPct,
            relatedThresholdPct: bands.shelfEntryPct, kind: .shelfBoundary, comparison: .atOrBelow,
            summary: "An existing Hold releases at or below \(percent(bands.shelfMinPct)).",
            detail: "Hold is retained only while fill is strictly above this lower boundary. Re-entering Hold uses a separate, higher threshold, so the same fill can correspond to different stages depending on history. A colored shelf alone cannot identify the recorded stage.",
            sourceRelativePath: overfill, sourceLine: 70, styleRole: .shelf
        )]
        if let entry = bands.shelfEntryPct {
            zones.append(ReferenceZone(
                id: "hold-entry", title: "Hold enters", thresholdPct: entry,
                relatedThresholdPct: bands.shelfMinPct, kind: .transition, comparison: .atOrAbove,
                summary: "Enter Hold at or above \(percent(entry)) when higher stages do not apply.",
                detail: "On a rising path from Recovery, Hold starts here; on a falling path an existing Hold can continue down to its lower release boundary. Stage selection gives Discharge and Elevated priority. This gap prevents a small reversal from immediately toggling the stage.",
                sourceRelativePath: overfill, sourceLine: 70, styleRole: .hysteresis
            ))
        }
        zones.append(ReferenceZone(
            id: "target", title: "Reference center", thresholdPct: bands.targetPct,
            relatedThresholdPct: piOnset, kind: .target, comparison: .reference,
            summary: "\(percent(bands.targetPct)) is the configured fill reference, not a hard clamp.",
            detail: "The structural PI measures error relative to its \(percent(configuration.targetFillPct)) target. Its proportional error is one-sided: max(fill − target − \(number(configuration.deadbandPct)), 0). The regulator also uses stage, fill slope, scaffold and recovery state; a position relative to the center does not determine the applied action.",
            sourceRelativePath: scaffold, sourceLine: 1655, styleRole: .target
        ))
        if let release = bands.elevatedReleasePct {
            zones.append(ReferenceZone(
                id: "elevated-release", title: "Elevated releases", thresholdPct: release,
                relatedThresholdPct: bands.shelfMaxPct, kind: .transition, comparison: .atOrBelow,
                summary: "An existing Elevated releases at or below \(percent(release)).",
                detail: "Elevated remains active strictly above this release boundary, even after fill drops below its entry threshold. Discharge has its own higher-priority state and release test. The source also begins blending Hold and Elevated guard settings at this boundary, rather than switching every command abruptly.",
                sourceRelativePath: overfill, sourceLine: 79, styleRole: .hysteresis
            ))
        }
        zones.append(ReferenceZone(
            id: "elevated-entry", title: "Elevated enters", thresholdPct: bands.shelfMaxPct,
            relatedThresholdPct: bands.elevatedReleasePct, kind: .transition, comparison: .atOrAbove,
            summary: "Enter Elevated at or above \(percent(bands.shelfMaxPct)), unless Discharge takes priority.",
            detail: "This is the upper Hold reference. Between the inspected source's soft and strong drain thresholds, rising fill requests a small scaffold drain; flat or falling fill suppresses that soft drain. Guard commands also blend across the transition. Historical fill alone does not reveal whether these conditions or this controller mode applied.",
            sourceRelativePath: overfill, sourceLine: 79, styleRole: .shelf
        ))
        zones.append(ReferenceZone(
            id: "pi-onset", title: "PI error starts above", thresholdPct: piOnset,
            relatedThresholdPct: configuration.targetFillPct, kind: .piThreshold, comparison: .strictlyAbove,
            summary: "New proportional error and integral growth begin strictly above \(percent(piOnset)).",
            detail: "The +\(number(configuration.deadbandPct))-point allowance is one-sided, not a symmetric ± band. At or below this line, normalized error is zero and existing integral decays per step; the separate drain and recovery policies can still act. P = \(number(configuration.kp)) × normalized error; I = \(number(configuration.ki)) × accumulated error; the PI sum is capped at \(number(configuration.maxOutput)). Applied drainage can exceed that PI cap through policy floors.",
            sourceRelativePath: scaffold, sourceLine: 1655, styleRole: .pi
        ))
        zones.append(ReferenceZone(
            id: "strong-rail", title: "Strong rail", thresholdPct: bands.strongRailPct,
            relatedThresholdPct: nil, kind: .strongRail, comparison: .atOrAbove,
            summary: "At or above \(percent(bands.strongRailPct)), the inspected policy requests strong drainage.",
            detail: "With the structural controller active, the strong policy imposes at least 0.24 drain weight regardless of rising or falling slope. Its output blends sensory covariance toward a drain matrix; this is not liquid removal or a count of lost memories. Additional application and restart policies can alter the applied weight. This rail is a protective response threshold, not a proven stability boundary.",
            sourceRelativePath: scaffold, sourceLine: 1467, styleRole: .strong
        ))
        zones.append(ReferenceZone(
            id: "force-rail", title: "Force / warning rail", thresholdPct: bands.forceRailPct,
            relatedThresholdPct: bands.shelfMaxPct, kind: .warningRail, comparison: .atOrAbove,
            summary: "At \(percent(bands.forceRailPct)), extra gate/filter loosening has tapered to zero.",
            detail: "The source names this the force rail and uses it as the start of the stable-core warning range. Bounded gate opening and filter relaxation taper from the upper shelf to zero here. It is not the structural PI's forced-drain threshold: that separate policy begins at 82%, also the Discharge entry. This warning does not establish a guaranteed safe/unsafe divide.",
            sourceRelativePath: "minime/src/runtime/entrypoint.rs", sourceLine: 371, styleRole: .force
        ))
        return zones.sorted {
            $0.thresholdPct == $1.thresholdPct ? $0.id < $1.id : $0.thresholdPct < $1.thresholdPct
        }
    }

    private static func number(_ value: Double) -> String {
        String(format: "%.3f", locale: Locale(identifier: "en_US_POSIX"), value)
            .replacingOccurrences(of: "0+$", with: "", options: .regularExpression)
            .replacingOccurrences(of: "\\.$", with: "", options: .regularExpression)
    }

    private static func percent(_ value: Double) -> String { "\(number(value))%" }
}
