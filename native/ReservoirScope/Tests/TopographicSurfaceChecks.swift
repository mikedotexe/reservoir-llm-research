// Synthetic mapping checks, concatenated with StateSurface.swift by the check script.
import Foundation
import CryptoKit

private var passed = 0
@MainActor private func check(_ condition: Bool, _ description: String) {
    guard condition else { fputs("FAIL: \(description)\n", stderr); exit(1) }
    passed += 1
    print("PASS \(passed): \(description)")
}
private func rejects(_ operation: () throws -> Void) -> Bool {
    do { try operation(); return false } catch { return true }
}
private func close(_ a: Double, _ b: Double, _ tolerance: Double = 2e-7) -> Bool { abs(a - b) <= tolerance }
private struct Fingerprint {
    var data = Data()
    mutating func integer<T: FixedWidthInteger>(_ value: T) {
        var bytes = value.bigEndian
        withUnsafeBytes(of: &bytes) { data.append(contentsOf: $0) }
    }
    mutating func vector(_ value: SIMD3<Float>) {
        integer(value.x.bitPattern); integer(value.y.bitPattern); integer(value.z.bitPattern)
    }
    mutating func triangle(_ value: SIMD3<UInt32>) { integer(value.x); integer(value.y); integer(value.z) }
    mutating func atlas(_ atlas: StateSurfaceAtlas) {
        integer(UInt64(atlas.coordinateCount)); data.append(contentsOf: atlas.layoutVersion.utf8)
        for value in atlas.sites { vector(value) }
        for value in atlas.unitVertices { vector(value) }
        for value in atlas.triangles { triangle(value) }
        for value in atlas.interpolationWeights { integer(value.bitPattern) }
        for value in atlas.cutBoundary { integer(value) }
        for value in atlas.backTriangles { triangle(value) }
        for value in atlas.frontTriangles { triangle(value) }
        for value in atlas.siteTriangleIndices { integer(UInt64(value)) }
        integer(atlas.unitVolume.bitPattern)
    }
    mutating func mesh(_ mesh: StateSurfaceMesh) {
        for value in mesh.positions { vector(value) }
        for value in mesh.normals { vector(value) }
        for value in mesh.fieldValues { integer(value.bitPattern) }
        for value in mesh.sitePositions { vector(value) }
        for value in [mesh.referenceRadius, mesh.requestedRelief, mesh.appliedRelief, mesh.volume, mesh.targetVolume] {
            integer(value.bitPattern)
        }
        data.append(contentsOf: (mesh.fallbackReason ?? "nil").utf8)
    }
    var sha256: String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
}

private func legacyFingerprint() throws -> String {
    var fingerprint = Fingerprint()
    for count in [32, 128] {
        let atlas = try StateSurfaceAtlas(nodeCount: count)
        fingerprint.atlas(atlas)
        var opposite = Array(repeating: 0.0, count: count)
        opposite[0] = 1; opposite[count - 1] = -1
        let fixtures = [Array(repeating: 0.75, count: count), opposite, atlas.sites.map { Double($0.x) }]
        for values in fixtures {
            for fill in [0.0, 0.000001, 0.1, 50, 68, 95, 100] {
                fingerprint.mesh(try StateSurfaceMath.mesh(atlas: atlas, values: values, scale: -1...1,
                    fillPct: fill, relief: 0.35))
            }
        }
    }
    return fingerprint.sha256
}

// BEGIN CHECKS
// Captured from the unmodified 0.9.0 StateSurface.swift on this arm64 macOS host,
// using the same Swift 6 optimized compiler and the function above. It covers both
// original atlases and 42 fill-constrained meshes, including every emitted array.
let legacySHA256 = "38b9d68778ae90292e173b4c9a9c1c6eeab476e4c6a0253dae7ee450ac801bce"
check(try legacyFingerprint() == legacySHA256,
    "Original 32/128-coordinate atlases and all 42 legacy meshes retain their exact numerical fingerprint")
let original = StateSurfaceAtlas.standard
let default32 = try StateSurfaceAtlas(nodeCount: 32)
let dense = try StateSurfaceAtlas(nodeCount: 32, rows: 64, columns: 128)
check(original.layoutVersion == StateSurfaceAtlas.version && original.rows == 32 && original.columns == 64
    && original.unitVertices.count == 1986 && original.triangles.count == 3968,
    "The default native atlas retains its version and original resolution")
check(dense.layoutVersion == "index-fibonacci-32-r64-c128-v1" && dense.sites == default32.sites
    && dense.unitVertices.count == 8066 && dense.triangles.count == 16128,
    "Dense topography samples the same 32 fixed coordinate sites and records its distinct resolution")
let denseAgain = try StateSurfaceAtlas(nodeCount: 32, rows: 64, columns: 128)
check(dense.unitVertices == denseAgain.unitVertices && dense.triangles == denseAgain.triangles
    && dense.interpolationWeights == denseAgain.interpolationWeights
    && dense.siteTriangleIndices == denseAgain.siteTriangleIndices,
    "Atlas geometry, kernel rows and picking triangles are deterministic")

var edgeCounts: [String: Int] = [:]
var directedEdges = Set<String>()
for triangle in dense.triangles {
    for (a, b) in [(triangle.x, triangle.y), (triangle.y, triangle.z), (triangle.z, triangle.x)] {
        edgeCounts["\(min(a, b)),\(max(a, b))", default: 0] += 1
        directedEdges.insert("\(a),\(b)")
    }
}
check(edgeCounts.values.allSatisfy { $0 == 2 } && directedEdges.count == dense.triangles.count * 3
    && dense.unitVertices.count - edgeCounts.count + dense.triangles.count == 2,
    "The dense mesh is closed, consistently wound and seam-free with spherical Euler characteristic")
check(dense.backTriangles.count + dense.frontTriangles.count == dense.triangles.count
    && dense.cutBoundary.count == 128 && Set(dense.cutBoundary).count == 128
    && dense.cutBoundary.allSatisfy { dense.unitVertices[Int($0)].z == 0 },
    "Cutaway triangles share an exact planar 128-vertex boundary without seam duplicates")
var maximumKernelError = 0.0
for vertex in dense.unitVertices.indices {
    let direction = simd_normalize(SIMD3<Double>(dense.unitVertices[vertex]))
    let row = dense.sites.map { exp(24 * (simd_dot(direction, simd_normalize(SIMD3<Double>($0))) - 1)) }
    let total = row.reduce(0, +)
    for node in dense.sites.indices {
        maximumKernelError = max(maximumKernelError,
            abs(Double(dense.interpolationWeights[vertex * 32 + node]) - row[node] / total))
    }
}
check(maximumKernelError < 3e-8,
    "Every dense interpolation weight matches the original normalized spherical Gaussian with kernel 24")

let zeros = Array(repeating: 0.0, count: 32)
let zero = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: -1...1)
check(zero.positions == dense.unitVertices.map { SIMD3<Float>(SIMD3<Double>($0) * 0.82) }
    && zero.fieldValues.allSatisfy { $0 == 0 } && zero.referenceRadius == 0.82,
    "A zero state produces the exact fixed neutral radius without invented structure")
let positive = try StateSurfaceMath.topographicMesh(atlas: dense, values: Array(repeating: 1, count: 32), scale: -1...1)
let negative = try StateSurfaceMath.topographicMesh(atlas: dense, values: Array(repeating: -1, count: 32), scale: -1...1)
check(positive.positions.allSatisfy { close(simd_length(SIMD3<Double>($0)), 0.98) }
    && negative.positions.allSatisfy { close(simd_length(SIMD3<Double>($0)), 0.66) },
    "Constant positive and negative fields create peaks at radius 0.98 and valleys at 0.66")
check(negative.volume < zero.volume && zero.volume < positive.volume
    && [negative, zero, positive].allSatisfy { $0.volume == $0.targetVolume && $0.fallbackReason == nil },
    "Topographic volume changes with signed state; the compatibility field records measured volume without constraining it")

let spatial = dense.sites.map { Double($0.x) }
let surface = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial, scale: -1...1)
let reversed = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial.map { -$0 }, scale: -1...1)
let field = try dense.interpolate(spatial)
check(surface.fieldValues == field && surface.positions.indices.allSatisfy { index in
    let expected = 0.82 + 0.16 * min(1, max(-1, Double(field[index])))
    return close(simd_length(SIMD3<Double>(surface.positions[index])), expected)
}, "Each rendered radius directly follows the unchanged signed interpolated field and fixed scale")
check(surface.positions.indices.allSatisfy { index in
    let a = simd_length(SIMD3<Double>(surface.positions[index]))
    let b = simd_length(SIMD3<Double>(reversed.positions[index]))
    return close(a + b, 1.64)
} && surface.positions.contains { simd_length($0) < 0.75 }
    && surface.positions.contains { simd_length($0) > 0.89 },
    "Negating the same coordinates reverses the relief around the neutral sphere")
let tiny = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial.map { $0 * 0.01 }, scale: -1...1)
let wide = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial, scale: -2...2)
check(surface.positions.indices.allSatisfy { index in
    let ordinary = simd_length(SIMD3<Double>(surface.positions[index])) - 0.82
    let smaller = simd_length(SIMD3<Double>(tiny.positions[index])) - 0.82
    let wider = simd_length(SIMD3<Double>(wide.positions[index])) - 0.82
    return close(smaller, ordinary * 0.01) && close(wider, ordinary * 0.5)
}, "Small signals stay small and wider declared scales reduce relief without normalizing a frame")
let noRelief = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial, scale: -1...1, relief: 0)
let maximum = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial, scale: -1...1, relief: 0.20)
check(noRelief.positions == zero.positions && noRelief.fieldValues == surface.fieldValues
    && maximum.appliedRelief == 0.20 && maximum.requestedRelief == 0.20,
    "Zero gain removes only geometry and requested relief applies directly without hidden backoff")
let oversized = try StateSurfaceMath.topographicMesh(atlas: dense, values: Array(repeating: 4, count: 32), scale: -1...1)
let exact = try StateSurfaceMath.field(.signedActivation, activations: Array(repeating: 4, count: 32))
check(zip(oversized.positions, positive.positions).allSatisfy { simd_length($0 - $1) < 2e-7 }
    && oversized.fieldValues.allSatisfy { close(Double($0), 4, 5e-7) }
    && exact.values.allSatisfy { $0 == 4 } && exact.outOfRangeCount == 32,
    "Relief alone clamps out-of-range values; the field and exact inspector retain their original magnitude")

let meshes = [zero, positive, negative, surface, reversed, tiny, wide, noRelief, maximum, oversized]
check(meshes.allSatisfy { mesh in
    mesh.positions.enumerated().allSatisfy { index, point in
        let length = simd_length(SIMD3<Double>(point)), normal = mesh.normals[index]
        return length.isFinite && (0.62 - 2e-7...1.02 + 2e-7).contains(length)
            && normal.x.isFinite && normal.y.isFinite && normal.z.isFinite
            && close(simd_length(SIMD3<Double>(normal)), 1) && simd_dot(normal, point) > 0
    }
}, "All fixtures have finite bounded radii and unit outward normals computed from their rendered triangles")
check(meshes.allSatisfy { mesh in
    mesh.sitePositions.enumerated().allSatisfy { index, point in
        let triangle = dense.triangles[dense.siteTriangleIndices[index]]
        let a = SIMD3<Double>(mesh.positions[Int(triangle.x)])
        let b = SIMD3<Double>(mesh.positions[Int(triangle.y)])
        let c = SIMD3<Double>(mesh.positions[Int(triangle.z)])
        let p = SIMD3<Double>(point), ray = SIMD3<Double>(dense.sites[index])
        let normal = simd_normalize(simd_cross(b - a, c - a))
        let barycentric = simd_double3x3(columns: (a, b, c)).inverse * p
        return abs(simd_dot(p - a, normal)) < 2e-7 && simd_length(simd_cross(p, ray)) < 2e-7
            && simd_dot(p, ray) > 0 && min(barycentric.x, min(barycentric.y, barycentric.z)) >= -2e-6
            && close(barycentric.x + barycentric.y + barycentric.z, 1, 2e-6)
    }
}, "Every picking site lies on its actual containing triangle and original indexed ray, including valleys")
check(meshes.allSatisfy { mesh in
    dense.cutBoundary.allSatisfy { mesh.positions[Int($0)].z == 0 }
        && close(StateSurfaceMath.signedVolume(positions: mesh.positions, triangles: dense.backTriangles)
            + StateSurfaceMath.signedVolume(positions: mesh.positions, triangles: dense.frontTriangles), mesh.volume, 1e-10)
}, "Relief preserves the closed mesh and exact cutaway seam, with both halves summing to its measured volume")
let duplicate = try StateSurfaceMath.topographicMesh(atlas: dense, values: spatial, scale: -1...1)
check(surface.positions == duplicate.positions && surface.normals == duplicate.normals
    && surface.sitePositions == duplicate.sitePositions && surface.volume == duplicate.volume,
    "Repeated observations give identical geometry, normals and picking positions without animation inputs")
let implicit = try StateSurfaceMath.topographicMesh(values: zeros, scale: -1...1)
check(implicit.positions.count == default32.unitVertices.count && implicit.sitePositions.count == 32,
    "The optional atlas defaults to the compatible original resolution with the actual coordinate count")
check(rejects { _ = try StateSurfaceAtlas(nodeCount: 32, rows: 63, columns: 128) }
    && rejects { _ = try StateSurfaceAtlas(nodeCount: 32, rows: 64, columns: 129) }
    && rejects { _ = try StateSurfaceAtlas(nodeCount: 32, rows: 66, columns: 128) }
    && rejects { _ = try StateSurfaceAtlas(nodeCount: 32, rows: 2, columns: 4) },
    "Unsupported atlas resolutions fail before allocating a mesh")
check(rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: -1...1, relief: 0.21) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: -1...1, relief: -.infinity) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: -1...1, relief: .nan) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: 0...0) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: zeros, scale: -1...Double.infinity) },
    "Invalid topographic gain and scales fail explicitly")
check(rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: [1], scale: -1...1) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(values: [], scale: -1...1) }
    && rejects { _ = try StateSurfaceMath.topographicMesh(atlas: dense, values: Array(repeating: .nan, count: 32), scale: -1...1) },
    "Malformed or non-finite coordinate fields cannot become visible topography")
print("\(passed) topographic surface checks passed; \(meshes.count) synthetic meshes; legacy SHA256 \(legacySHA256).")
