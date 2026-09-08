import Foundation

/// Pure checks of annotation semantics. These do not simulate a controller or
/// assign a historical stage; the existing evidence harness reports the results.
func referenceZoneChecks(bands: ReferenceBands, configuration: StructuralPIConfiguration)
    -> [(condition: Bool, description: String)] {
    let zones = ReferenceZone.catalog(bands: bands, configuration: configuration)
    let byID = Dictionary(zones.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    let onset = configuration.targetFillPct + configuration.deadbandPct
    let pi = byID["pi-onset"]
    let elevated = byID["elevated-entry"]

    let shiftedBands = ReferenceBands(
        shelfMinPct: 52, shelfEntryPct: 55, targetPct: 63, shelfMaxPct: 70,
        elevatedReleasePct: 69, strongRailPct: 76, forceRailPct: 84, status: nil, note: nil
    )
    let shiftedConfig = StructuralPIConfiguration(
        targetFillPct: 66, deadbandPct: 3.5, kp: 0.5, ki: 0.03,
        maxOutput: 0.15, integralDecayPerStep: 0.8
    )
    let shifted = ReferenceZone.catalog(bands: shiftedBands, configuration: shiftedConfig)
    let shiftedByID = Dictionary(shifted.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    let shiftedExpected: [String: Double] = [
        "shelf-release": 52, "hold-entry": 55, "target": 63,
        "elevated-release": 69, "elevated-entry": 70,
        "pi-onset": 69.5, "strong-rail": 76, "force-rail": 84,
    ]

    let withoutHysteresis = ReferenceBands(
        shelfMinPct: bands.shelfMinPct, shelfEntryPct: nil, targetPct: bands.targetPct,
        shelfMaxPct: bands.shelfMaxPct, elevatedReleasePct: nil,
        strongRailPct: bands.strongRailPct, forceRailPct: bands.forceRailPct,
        status: nil, note: nil
    )
    let partial = ReferenceZone.catalog(bands: withoutHysteresis, configuration: configuration)

    return [
        (Set(zones.map(\.id)).count == zones.count && zones.allSatisfy { $0.sourceLine > 0 && !$0.sourceRelativePath.isEmpty },
         "Reference annotations preserve distinct identities and inspectable source anchors"),
        (pi?.thresholdPct == onset && pi?.comparison == .strictlyAbove
            && pi?.matchesThreshold(onset) == false
            && pi?.matchesThreshold(onset.nextUp) == true
            && pi?.matchesThreshold(configuration.targetFillPct - configuration.deadbandPct) == false
            && zones.filter { $0.kind == .piThreshold }.count == 1,
         "Structural PI allowance is one-sided and begins strictly above target plus allowance"),
        (elevated?.thresholdPct == bands.shelfMaxPct && elevated?.comparison == .atOrAbove
            && elevated?.matchesThreshold(bands.shelfMaxPct) == true
            && elevated?.matchesThreshold(bands.shelfMaxPct.nextDown) == false
            && pi?.id != elevated?.id && pi?.kind != elevated?.kind,
         "Coincident Elevated and PI references retain different equality rules and meanings"),
        (byID["shelf-release"]?.matchesThreshold(bands.shelfMinPct) == true
            && byID["shelf-release"]?.matchesThreshold(bands.shelfMinPct.nextUp) == false
            && byID["hold-entry"]?.relatedThresholdPct == bands.shelfMinPct
            && byID["elevated-release"]?.comparison == .atOrBelow,
         "Hysteresis release includes equality and stays distinct from re-entry"),
        (shiftedExpected.allSatisfy { shiftedByID[$0.key]?.thresholdPct == $0.value }
            && shiftedByID["pi-onset"]?.relatedThresholdPct == shiftedConfig.targetFillPct,
         "Every plotted position follows supplied evidence, including independently configured PI target"),
        (!partial.contains { $0.id == "hold-entry" || $0.id == "elevated-release" }
            && partial.count == 6 && partial.first { $0.id == "shelf-release" }?.relatedThresholdPct == nil,
         "Missing optional hysteresis values remain absent instead of acquiring invented thresholds"),
        (zones.allSatisfy { !$0.matchesThreshold(.nan) && !$0.matchesThreshold(.infinity) },
         "Invalid scalar observations cannot satisfy reference-boundary comparisons"),
    ]
}
