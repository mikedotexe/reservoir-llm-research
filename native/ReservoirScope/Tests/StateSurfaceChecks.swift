// Concatenated with the production implementation by check-state-surface.sh.
// Synthetic fixtures only: these are mapping invariants, not reservoir findings.
import Foundation

private var passed = 0
@MainActor private func check(_ condition: Bool, _ description: String) {
    guard condition else { fputs("FAIL: \(description)\n", stderr); exit(1) }
    passed += 1
    print("PASS \(passed): \(description)")
}
private func close(_ a: Double, _ b: Double, tolerance: Double = 1e-10) -> Bool { abs(a - b) <= tolerance }
private func rejects(_ operation: () throws -> Void) -> Bool { do { try operation(); return false } catch { return true } }
private func maxError(_ a: [Double], _ b: [Double]) -> Double { zip(a, b).map { abs($0 - $1) }.max() ?? 0 }
private func node(_ index: Int, _ value: Double = 1) -> [Double] {
    var values = Array(repeating: 0.0, count: 128); values[index] = value; return values
}

let atlas = StateSurfaceAtlas.standard
check(atlas.sites.count == 128 && Set(atlas.sites).count == 128 && atlas.sites.allSatisfy {
    abs(simd_length($0) - 1) < 2e-7
}, "The versioned atlas has 128 distinct permanent unit directions")
check(atlas.unitVertices.count == 1986 && atlas.triangles.count == 3968,
    "The bounded sphere uses 1,986 shared vertices and 3,968 triangles")
var edgeCounts: [String: Int] = [:]
var directedEdges: Set<String> = []
for triangle in atlas.triangles {
    for (a, b) in [(triangle.x, triangle.y), (triangle.y, triangle.z), (triangle.z, triangle.x)] {
        edgeCounts["\(min(a, b)),\(max(a, b))", default: 0] += 1
        directedEdges.insert("\(a),\(b)")
    }
}
check(edgeCounts.values.allSatisfy { $0 == 2 } && directedEdges.count == atlas.triangles.count * 3
    && atlas.unitVertices.count - edgeCounts.count + atlas.triangles.count == 2,
    "The mesh is closed and consistently oriented, with the Euler characteristic of a sphere")
check(atlas.unitVolume > 0 && abs(atlas.unitVolume - 4 * .pi / 3) / (4 * .pi / 3) < 0.01,
    "Unit mesh volume is positive and within 1% of the ideal sphere; these are distinct quantities")
check(atlas.backTriangles.count + atlas.frontTriangles.count == atlas.triangles.count
    && atlas.cutBoundary.count == 64 && atlas.cutBoundary.allSatisfy { atlas.unitVertices[Int($0)].z == 0 },
    "Cutaway halves share the same full mesh and an exact 64-vertex planar boundary")
check(atlas.interpolationWeights.count == atlas.unitVertices.count * 128
    && atlas.interpolationWeights.allSatisfy { $0.isFinite && $0 >= 0 }
    && atlas.unitVertices.indices.allSatisfy { index in
        let sum = atlas.interpolationWeights[(index * 128)..<((index + 1) * 128)].reduce(0.0) { $0 + Double($1) }
        return abs(sum - 1) < 5e-8
    }, "Every fixed interpolation row has nonnegative weights summing to one within Float precision")
let constant = try StateSurfaceMath.field(.signedActivation, activations: Array(repeating: 0.75, count: 128))
let constantBlend = try atlas.interpolate(constant.values)
check(constantBlend.allSatisfy { abs($0 - 0.75) < 1e-7 }, "Interpolation preserves a constant field")
let impulse = try StateSurfaceMath.field(.signedActivation, activations: node(9))
let impulseBlend = try atlas.interpolate(impulse.values)
check(impulse.values[9] == 1 && impulse.values.filter { $0 != 0 }.count == 1
    && impulseBlend.allSatisfy { $0 >= 0 && $0 <= 1 },
    "A one-coordinate fixture preserves the exact node while its contextual blend remains bounded")
var oppositeValues = node(9); oppositeValues[10] = -1
let opposite = try StateSurfaceMath.field(.signedActivation, activations: oppositeValues)
let magnitude = try StateSurfaceMath.field(.magnitude, activations: oppositeValues)
check(opposite.values[9] == 1 && opposite.values[10] == -1
    && magnitude.values[9] == 1 && magnitude.values[10] == 1,
    "Opposite signs remain exact and the magnitude view preserves both contributions")
let oppositeBlend = try atlas.interpolate(opposite.values), magnitudeBlend = try atlas.interpolate(magnitude.values)
check(zip(oppositeBlend, magnitudeBlend).allSatisfy { abs($0) <= $1 + 1e-7 }
    && zip(oppositeBlend, magnitudeBlend).contains { abs($0) < $1 - 1e-4 },
    "Signed interpolation can cancel; magnitude exposes variation hidden by that cancellation")
let tiny = try StateSurfaceMath.field(.signedActivation, activations: node(9, 0.0001))
let oversized = try StateSurfaceMath.field(.signedActivation, activations: node(9, 2))
check(impulse.scale == tiny.scale && tiny.scale == oversized.scale && oversized.outOfRangeCount == 1
    && oversized.values[9] == 2, "Fixed scales never normalize a frame and out-of-range exact values remain available")

let mean = Array(repeating: 0.2, count: 128), basis = [node(0), node(1), node(2)]
var observed = mean; observed[0] += 0.3; observed[1] += 0.4; observed[3] += 0.5
let projected = try StateSurfaceMath.field(.reconstruction, activations: observed, mean: mean,
    components: basis, selectedModes: [0, 1])
let omitted = try StateSurfaceMath.field(.residual, activations: observed, mean: mean,
    components: basis, selectedModes: [0, 1])
let deviation = try StateSurfaceMath.field(.referenceDeviation, activations: observed, mean: mean)
check(close(projected.values[0], 0.3) && close(projected.values[1], 0.4) && projected.values[3] == 0
    && close(omitted.values[3], 0.5) && maxError(zip(projected.values, omitted.values).map(+), deviation.values) < 1e-12,
    "Selected reconstruction plus residual recovers every reference-centered coordinate")
check(close(projected.centeredEnergy!, 0.5) && close(projected.reconstructedEnergy!, 0.25)
    && close(projected.residualEnergy!, 0.25), "Orthonormal reconstruction splits squared distance without losing the omitted energy")
let inSpan = try StateSurfaceMath.field(.residual, activations: node(0, 0.6), mean: Array(repeating: 0, count: 128),
    components: basis, selectedModes: [0])
let perpendicular = try StateSurfaceMath.field(.residual, activations: node(3, 0.6), mean: Array(repeating: 0, count: 128),
    components: basis, selectedModes: [0])
check(inSpan.values.allSatisfy { $0 == 0 } && perpendicular.values == node(3, 0.6),
    "A state in the selected span has zero residual; a perpendicular state remains entirely omitted")
let flipped = try StateSurfaceMath.field(.reconstruction, activations: observed, mean: mean,
    components: basis.map { $0.map { -$0 } }, selectedModes: [0, 1])
check(maxError(flipped.values, projected.values) < 1e-12 && close(flipped.scores[0], -projected.scores[0]),
    "Reversing component signs reverses scores and leaves the reconstructed surface unchanged")
let emptyModes = try StateSurfaceMath.field(.residual, activations: observed, mean: mean, components: basis, selectedModes: [])
check(emptyModes.values == deviation.values && emptyModes.reconstructedEnergy == 0,
    "Selecting no modes leaves the entire deviation in the omitted component")
check(rejects { _ = try StateSurfaceMath.field(.signedActivation, activations: [0]) }
    && rejects { _ = try StateSurfaceMath.field(.signedActivation, activations: node(0, .nan)) }
    && rejects { _ = try StateSurfaceMath.field(.signedActivation, activations: node(0, Double.greatestFiniteMagnitude)) }
    && rejects { _ = try StateSurfaceMath.field(.residual, activations: node(0)) },
    "Invalid dimensions, non-finite or Float-overflow state and missing required reference are rejected")
check(rejects { _ = try StateSurfaceMath.field(.reconstruction, activations: node(0), mean: mean,
        components: [node(0), node(0)], selectedModes: [0]) }
    && rejects { _ = try StateSurfaceMath.field(.reconstruction, activations: node(0), mean: mean,
        components: basis, selectedModes: [3]) },
    "Non-orthonormal references and unavailable selected modes cannot silently change the field")

let spatialValues = atlas.sites.map { Double($0.x) }
let spatial = try StateSurfaceMath.field(.signedActivation, activations: spatialValues)
let fills = [0.0, 0.000001, 0.1, 1, 20, 50, 68, 74, 78, 95, 99.9, 99.999999, 100]
let fixtures = [constant, opposite, spatial, oversized]
var checkedMeshes = 0, maxRelativeVolumeError = 0.0, actualReliefSeen = false
var allVolumes = true, allContained = true, allNormals = true, allMarkers = true, allEndpoints = true
for fixture in fixtures {
    for fill in fills {
        let mesh = try StateSurfaceMath.mesh(field: fixture, fillPct: fill, relief: 0.35)
        checkedMeshes += 1
        let relativeError = mesh.targetVolume > 0 ? abs(mesh.volume - mesh.targetVolume) / mesh.targetVolume : abs(mesh.volume)
        maxRelativeVolumeError = max(maxRelativeVolumeError, relativeError)
        allVolumes = allVolumes && relativeError <= 2e-6 && mesh.fallbackReason == nil
        allContained = allContained && mesh.positions.allSatisfy {
            let length = simd_length(SIMD3<Double>($0))
            return length <= 1 + 2e-7 && (fill == 0 ? length == 0 : length > 0)
        }
        allNormals = allNormals && mesh.normals.enumerated().allSatisfy { index, normal in
            abs(simd_length(normal) - 1) < 2e-7 && (fill == 0 || simd_dot(normal, mesh.positions[index]) > 0)
        }
        allMarkers = allMarkers && mesh.sitePositions.enumerated().allSatisfy { index, point in
            guard fill > 0 else { return point == .zero }
            let triangle = atlas.triangles[atlas.siteTriangleIndices[index]]
            let a = mesh.positions[Int(triangle.x)], b = mesh.positions[Int(triangle.y)], c = mesh.positions[Int(triangle.z)]
            let normal = simd_normalize(simd_cross(b - a, c - a))
            return abs(simd_dot(point - a, normal)) < 2e-7
                && simd_length(simd_cross(point, atlas.sites[index])) < 2e-7
        }
        if fill == 0 || fill == 100 { allEndpoints = allEndpoints && mesh.appliedRelief == 0 }
        if fixture.field == .signedActivation && fill == 68 {
            let radii = mesh.positions.map { simd_length($0) }
            actualReliefSeen = actualReliefSeen || radii.max()! - radii.min()! > 0.02
        }
    }
}
check(allVolumes, "All 52 closed meshes preserve their measured fill volume within 2 parts per million")
check(allContained, "All 52 meshes remain within the container, with positive radii whenever fill is positive")
check(allNormals, "All 52 meshes have finite unit outward normals, including the empty endpoint fallback")
check(allMarkers, "Every node marker lies on its actual rendered triangle along its permanent atlas ray")
check(allEndpoints, "Empty and full fill explicitly flatten relief")
check(actualReliefSeen, "Intermediate fill has actual geometric displacement, not only a color change")
let deformed = try StateSurfaceMath.mesh(field: spatial, fillPct: 68, relief: 0.35)
let duplicate = try StateSurfaceMath.mesh(field: spatial, fillPct: 68, relief: 0.35)
check(deformed.positions == duplicate.positions && deformed.normals == duplicate.normals
    && deformed.fieldValues == duplicate.fieldValues, "Identical observations create identical geometry with no time-derived motion")
let flat = try StateSurfaceMath.mesh(field: spatial, fillPct: 68, relief: 0)
check(flat.positions == atlas.unitVertices.map { SIMD3<Float>(SIMD3<Double>($0) * cbrt(0.68)) }
    && flat.referenceRadius == deformed.referenceRadius && flat.appliedRelief == 0,
    "Turning relief off restores the exact undeformed mesh and preserves the independent measured reference")
let backVolume = StateSurfaceMath.signedVolume(positions: deformed.positions, triangles: atlas.backTriangles)
let frontVolume = StateSurfaceMath.signedVolume(positions: deformed.positions, triangles: atlas.frontTriangles)
check(close(backVolume + frontVolume, deformed.volume, tolerance: 1e-10)
    && atlas.cutBoundary.allSatisfy { deformed.positions[Int($0)].z == 0 },
    "Cutaway and complete views use one checked geometry; their planar caps add no origin-based tetrahedral volume")
check(rejects { _ = try StateSurfaceMath.mesh(field: spatial, fillPct: .nan) }
    && rejects { _ = try StateSurfaceMath.mesh(field: spatial, fillPct: 101) }
    && rejects { _ = try StateSurfaceMath.mesh(field: spatial, fillPct: 68, relief: -.infinity) },
    "Invalid fill and relief requests fail explicitly")
let rawMesh = try StateSurfaceMath.mesh(values: spatial.values, scale: spatial.scale, fillPct: 68, relief: 0.35)
let lowerReliefMesh = try StateSurfaceMath.mesh(values: spatial.values, scale: -1...1, fillPct: 50, relief: 0.08)
let widerScaleMesh = try StateSurfaceMath.mesh(values: spatial.values, scale: -2...2, fillPct: 50, relief: 0.08)
check(rawMesh.positions == deformed.positions && widerScaleMesh.positions != lowerReliefMesh.positions,
    "Renderer and typed-field APIs agree, and the declared fixed scale governs relief without frame normalization")
check(rejects { _ = try StateSurfaceMath.mesh(values: spatial.values, scale: 0...0, fillPct: 68) }
    && rejects { _ = try StateSurfaceMath.mesh(values: spatial.values, scale: -Double.infinity...1, fillPct: 68) },
    "A renderer cannot supply a zero-width or non-finite relief scale")
print("\(passed) state-surface checks passed; \(checkedMeshes) synthetic meshes; maximum relative volume error \(maxRelativeVolumeError).")
