import Foundation
import simd

// Usage:
// let values = try StateSurfaceMath.field(.signedActivation, activations: observedState)
// let mesh = try StateSurfaceMath.mesh(field: values, fillPct: observedFill, relief: 0.14)
// Upload mesh.positions/normals, StateSurfaceAtlas.standard.interpolationWeights,
// and values.values converted to Float. Metal computes the same weighted field
// as mesh.fieldValues. Use atlas.triangles, or atlas.backTriangles plus a cap
// triangulated from .zero and successive atlas.cutBoundary vertices. The cap's
// normal points toward +z; it is a section, not an interpolated surface field.
// Inspect values.values[index] exactly at mesh.sitePositions[index]. Preserve
// mesh.referenceRadius as the separate smooth fill reference. The atlas carries
// no source identity: a caller must label observed state, preview fill and fit
// provenance, including provisional live node-layout compatibility.

/// Every site is a native coordinate index, not an anatomical or connectivity map.
/// The version fixes the Fibonacci sites, mesh, kernel, and interpolation order.
struct StateSurfaceAtlas: Sendable {
    static let version = "index-fibonacci-128-v1"
    static let nodeCount = 128
    static let standard = StateSurfaceAtlas()
    let sites: [SIMD3<Float>]
    let unitVertices: [SIMD3<Float>]
    let triangles: [SIMD3<UInt32>]
    /// Row major [mesh vertex][node]. Directly uploadable to a Metal float buffer.
    let interpolationWeights: [Float]
    /// Indices on z = 0 in counterclockwise order as viewed from positive z.
    let cutBoundary: [UInt32]
    let backTriangles: [SIMD3<UInt32>]
    let frontTriangles: [SIMD3<UInt32>]
    /// Fixed containing triangle for each atlas ray; radial relief preserves these cones.
    let siteTriangleIndices: [Int]
    let unitVolume: Double

    private init() {
        let count = Self.nodeCount
        let goldenAngle = Double.pi * (3 - sqrt(5))
        sites = (0..<count).map { index in
            let y = 1 - 2 * (Double(index) + 0.5) / Double(count)
            let radius = sqrt(1 - y * y)
            let angle = goldenAngle * Double(index)
            return SIMD3(Float(radius * cos(angle)), Float(y), Float(radius * sin(angle)))
        }
        let rows = 32, columns = 64
        var vertices: [SIMD3<Float>] = [SIMD3(0, 1, 0)]
        for row in 1..<rows {
            let latitude = Double(row) * .pi / Double(rows)
            for column in 0..<columns {
                let longitude = Double(column) * 2 * .pi / Double(columns)
                var point = SIMD3(sin(latitude) * cos(longitude), cos(latitude), sin(latitude) * sin(longitude))
                for axis in 0..<3 where abs(point[axis]) < 1e-14 { point[axis] = 0 }
                vertices.append(SIMD3<Float>(point))
            }
        }
        let bottom = vertices.count
        vertices.append(SIMD3(0, -1, 0))
        func index(_ row: Int, _ column: Int) -> Int { 1 + (row - 1) * columns + column % columns }
        var faces: [SIMD3<UInt32>] = []
        func add(_ a: Int, _ b: Int, _ c: Int) {
            let pa = SIMD3<Double>(vertices[a]), pb = SIMD3<Double>(vertices[b]), pc = SIMD3<Double>(vertices[c])
            let face = simd_dot(pa, simd_cross(pb, pc)) > 0 ? SIMD3(UInt32(a), UInt32(b), UInt32(c))
                : SIMD3(UInt32(a), UInt32(c), UInt32(b))
            faces.append(face)
        }
        for column in 0..<columns {
            add(0, index(1, column), index(1, column + 1))
            for row in 1..<(rows - 1) {
                add(index(row, column), index(row + 1, column), index(row + 1, column + 1))
                add(index(row, column), index(row + 1, column + 1), index(row, column + 1))
            }
            add(index(rows - 1, column), bottom, index(rows - 1, column + 1))
        }
        unitVertices = vertices
        triangles = faces
        unitVolume = StateSurfaceMath.signedVolume(positions: vertices, triangles: faces)
        cutBoundary = vertices.indices.filter { vertices[$0].z == 0 }.sorted {
            atan2(vertices[$0].y, vertices[$0].x) < atan2(vertices[$1].y, vertices[$1].x)
        }.map(UInt32.init)
        backTriangles = faces.filter { vertices[Int($0.x)].z <= 0 && vertices[Int($0.y)].z <= 0 && vertices[Int($0.z)].z <= 0 }
        frontTriangles = faces.filter { vertices[Int($0.x)].z >= 0 && vertices[Int($0.y)].z >= 0 && vertices[Int($0.z)].z >= 0 }
        let inverseCones = faces.map { triangle in
            simd_double3x3(columns: (SIMD3<Double>(vertices[Int(triangle.x)]),
                SIMD3<Double>(vertices[Int(triangle.y)]), SIMD3<Double>(vertices[Int(triangle.z)]))).inverse
        }
        siteTriangleIndices = sites.map { site in
            let ray = SIMD3<Double>(site)
            // Every atlas direction belongs to one closed cone. This construction
            // is independent of observed values and is never recomputed per frame.
            return inverseCones.firstIndex { matrix in
                let weights = matrix * ray
                return min(weights.x, min(weights.y, weights.z)) >= -1e-10
            }!
        }
        var weights: [Float] = []
        weights.reserveCapacity(vertices.count * count)
        for vertex in vertices {
            let direction = simd_normalize(SIMD3<Double>(vertex))
            // A continuous spherical Gaussian; no moving nearest-neighbor boundary.
            let row = sites.map { exp(24 * (simd_dot(direction, simd_normalize(SIMD3<Double>($0))) - 1)) }
            let total = row.reduce(0, +)
            weights.append(contentsOf: row.map { Float($0 / total) })
        }
        interpolationWeights = weights
    }

    func interpolate(_ values: [Double]) throws -> [Float] {
        guard values.count == Self.nodeCount,
              values.allSatisfy({ $0.isFinite && Float($0).isFinite }) else { throw StateSurfaceError.invalidState }
        let interpolated = unitVertices.indices.map { vertex in
            let offset = vertex * Self.nodeCount
            var value = 0.0
            for node in 0..<Self.nodeCount { value += Double(interpolationWeights[offset + node]) * values[node] }
            return Float(value)
        }
        guard interpolated.allSatisfy(\.isFinite) else { throw StateSurfaceError.invalidState }
        return interpolated
    }
}

enum StateSurfaceField: String, CaseIterable, Identifiable, Sendable {
    case signedActivation, magnitude, referenceDeviation, reconstruction, residual
    var id: String { rawValue }
    var title: String {
        switch self {
        case .signedActivation: "Signed activation"
        case .magnitude: "Activation magnitude"
        case .referenceDeviation: "Change from reference"
        case .reconstruction: "Selected mode reconstruction"
        case .residual: "Omitted component"
        }
    }
    var requiresReference: Bool { self != .signedActivation && self != .magnitude }
    /// Fixed across all observations. Out-of-range values remain exact in the inspector.
    var scale: ClosedRange<Double> {
        switch self {
        case .signedActivation: -1...1
        case .magnitude: 0...1
        case .referenceDeviation, .reconstruction, .residual: -2...2
        }
    }
}

enum StateSurfaceError: Error, LocalizedError {
    case invalidState, invalidReference, invalidModes, invalidFill, invalidRelief, invalidScale
    var errorDescription: String? {
        switch self {
        case .invalidState: "A state surface requires 128 finite coordinate values."
        case .invalidReference: "This field requires a finite compatible reference and orthonormal components."
        case .invalidModes: "Selected modes must refer to the supplied frozen components."
        case .invalidFill: "Surface fill must be finite and between 0 and 100 percent."
        case .invalidRelief: "Relief must be finite and between 0 and 0.35."
        case .invalidScale: "The fixed surface scale requires finite, increasing limits."
        }
    }
}

struct StateSurfaceValues: Sendable {
    let field: StateSurfaceField
    let values: [Double]
    let activations: [Double]
    let centered: [Double]?
    let reconstruction: [Double]?
    let residual: [Double]?
    let scores: [Double]
    let selectedModes: [Int]
    let outOfRangeCount: Int
    let centeredEnergy: Double?
    let reconstructedEnergy: Double?
    let residualEnergy: Double?
    var scale: ClosedRange<Double> { field.scale }
}

struct StateSurfaceMesh: Sendable {
    let positions: [SIMD3<Float>]
    let normals: [SIMD3<Float>]
    let fieldValues: [Float]
    /// Exact ray intersections with the rendered triangles, in native index order.
    let sitePositions: [SIMD3<Float>]
    let referenceRadius: Double
    let requestedRelief: Double
    /// Actual radial coefficient after the endpoint envelope and containment backoff.
    let appliedRelief: Double
    let volume: Double
    let targetVolume: Double
    let fallbackReason: String?
}

enum StateSurfaceMath {
    /// References are only coordinate-compatible inputs here; the caller owns fit/layout provenance.
    static func field(_ field: StateSurfaceField, activations: [Double], mean: [Double]? = nil,
                      components: [[Double]]? = nil, selectedModes: [Int] = [0, 1, 2]) throws -> StateSurfaceValues {
        let count = StateSurfaceAtlas.nodeCount
        guard activations.count == count,
              activations.allSatisfy({ $0.isFinite && Float($0).isFinite }) else { throw StateSurfaceError.invalidState }
        var centered: [Double]?, reconstruction: [Double]?, residual: [Double]?
        var scores: [Double] = [], selection: [Int] = []
        if let mean {
            guard mean.count == count, mean.allSatisfy(\.isFinite) else { throw StateSurfaceError.invalidReference }
            centered = zip(activations, mean).map(-)
        }
        if let components {
            guard let centered, !components.isEmpty, components.count <= 3,
                  components.allSatisfy({ $0.count == count && $0.allSatisfy(\.isFinite) }) else {
                throw StateSurfaceError.invalidReference
            }
            for a in components.indices {
                for b in 0...a {
                    let dot = zip(components[a], components[b]).reduce(0) { $0 + $1.0 * $1.1 }
                    guard abs(dot - (a == b ? 1 : 0)) <= 1e-5 else { throw StateSurfaceError.invalidReference }
                }
            }
            selection = Array(Set(selectedModes)).sorted()
            guard selection.allSatisfy({ components.indices.contains($0) }) else { throw StateSurfaceError.invalidModes }
            scores = components.map { zip($0, centered).reduce(0) { $0 + $1.0 * $1.1 } }
            let projected = (0..<count).map { node in selection.reduce(0) { $0 + scores[$1] * components[$1][node] } }
            reconstruction = projected
            residual = zip(centered, projected).map(-)
        }
        let values: [Double]
        switch field {
        case .signedActivation: values = activations
        case .magnitude: values = activations.map(abs)
        case .referenceDeviation:
            guard let centered else { throw StateSurfaceError.invalidReference }; values = centered
        case .reconstruction:
            guard let reconstruction else { throw StateSurfaceError.invalidReference }; values = reconstruction
        case .residual:
            guard let residual else { throw StateSurfaceError.invalidReference }; values = residual
        }
        guard values.allSatisfy({ $0.isFinite && Float($0).isFinite }), centered?.allSatisfy(\.isFinite) ?? true,
              scores.allSatisfy(\.isFinite), reconstruction?.allSatisfy(\.isFinite) ?? true,
              residual?.allSatisfy(\.isFinite) ?? true else { throw StateSurfaceError.invalidState }
        func energy(_ vector: [Double]?) -> Double? { vector.map { $0.reduce(0) { $0 + $1 * $1 } } }
        return StateSurfaceValues(field: field, values: values, activations: activations, centered: centered,
            reconstruction: reconstruction, residual: residual, scores: scores, selectedModes: selection,
            outOfRangeCount: values.filter { !field.scale.contains($0) }.count,
            centeredEnergy: energy(centered), reconstructedEnergy: energy(reconstruction), residualEnergy: energy(residual))
    }

    /// CPU reference for the immutable mesh sent to Metal. No clock enters this mapping.
    /// Volume is measured on the complete closed triangle mesh, including in cutaway mode.
    static func mesh(atlas: StateSurfaceAtlas = .standard, field: StateSurfaceValues,
                     fillPct: Double, relief: Double = 0.14) throws -> StateSurfaceMesh {
        try mesh(atlas: atlas, values: field.values, scale: field.scale, fillPct: fillPct, relief: relief)
    }

    /// Lower-level renderer entry point when the observation already carries a
    /// validated derived field. Its declared fixed scale also controls relief.
    static func mesh(atlas: StateSurfaceAtlas = .standard, values: [Double], scale: ClosedRange<Double>,
                     fillPct: Double, relief: Double = 0.14) throws -> StateSurfaceMesh {
        guard fillPct.isFinite, (0...100).contains(fillPct) else { throw StateSurfaceError.invalidFill }
        guard relief.isFinite, (0...0.35).contains(relief) else { throw StateSurfaceError.invalidRelief }
        guard scale.lowerBound.isFinite, scale.upperBound.isFinite,
              scale.lowerBound < scale.upperBound else { throw StateSurfaceError.invalidScale }
        let interpolated = try atlas.interpolate(values)
        let fraction = fillPct / 100, radius = cbrt(fraction), target = fraction * atlas.unitVolume
        let fixedExtent = max(abs(scale.lowerBound), abs(scale.upperBound))
        let boundedField = interpolated.map { min(1, max(-1, Double($0) / fixedExtent)) }
        let base = atlas.unitVertices.map { SIMD3<Float>(SIMD3<Double>($0) * radius) }
        func result(_ positions: [SIMD3<Float>], gain: Double, fallback: String?) -> StateSurfaceMesh {
            let sitePositions = atlas.sites.enumerated().map { index, site -> SIMD3<Float> in
                guard fraction > 0 else { return .zero }
                let triangle = atlas.triangles[atlas.siteTriangleIndices[index]]
                let a = SIMD3<Double>(positions[Int(triangle.x)]), b = SIMD3<Double>(positions[Int(triangle.y)])
                let c = SIMD3<Double>(positions[Int(triangle.z)]), ray = SIMD3<Double>(site)
                let normal = simd_cross(b - a, c - a)
                return SIMD3<Float>(ray * (simd_dot(a, normal) / simd_dot(ray, normal)))
            }
            return StateSurfaceMesh(positions: positions, normals: normals(positions: positions, triangles: atlas.triangles,
                fallback: atlas.unitVertices), fieldValues: interpolated, sitePositions: sitePositions, referenceRadius: radius,
                requestedRelief: relief, appliedRelief: gain,
                volume: signedVolume(positions: positions, triangles: atlas.triangles), targetVolume: target,
                fallbackReason: fallback)
        }
        guard fraction > 0, fraction < 1, relief > 0 else { return result(base, gain: 0, fallback: nil) }
        var gain = relief * 4 * fraction * (1 - fraction)
        for _ in 0..<18 {
            let candidate = atlas.unitVertices.indices.map { index in
                SIMD3<Float>(SIMD3<Double>(atlas.unitVertices[index]) * radius * (1 + gain * boundedField[index]))
            }
            let volume = signedVolume(positions: candidate, triangles: atlas.triangles)
            if volume.isFinite, volume > 0 {
                let scale = cbrt(target / volume)
                let positions = candidate.map { SIMD3<Float>(SIMD3<Double>($0) * scale) }
                let measured = signedVolume(positions: positions, triangles: atlas.triangles)
                if positions.allSatisfy({ p in
                    let norm = simd_length(SIMD3<Double>(p))
                    return norm.isFinite && norm > 0 && norm <= 1 + 2e-7
                }), measured.isFinite, abs(measured - target) <= target * 2e-6 {
                    return result(positions, gain: gain, fallback: nil)
                }
            }
            gain *= 0.5
        }
        return result(base, gain: 0, fallback: "Relief was flattened because the checked mesh did not meet its volume and containment limits.")
    }

    static func signedVolume(positions: [SIMD3<Float>], triangles: [SIMD3<UInt32>]) -> Double {
        triangles.reduce(0) { volume, triangle in
            let a = SIMD3<Double>(positions[Int(triangle.x)]), b = SIMD3<Double>(positions[Int(triangle.y)])
            let c = SIMD3<Double>(positions[Int(triangle.z)])
            return volume + simd_dot(a, simd_cross(b, c)) / 6
        }
    }

    static func normals(positions: [SIMD3<Float>], triangles: [SIMD3<UInt32>],
                        fallback: [SIMD3<Float>]) -> [SIMD3<Float>] {
        var accumulated = Array(repeating: SIMD3<Double>.zero, count: positions.count)
        for triangle in triangles {
            let a = Int(triangle.x), b = Int(triangle.y), c = Int(triangle.z)
            let normal = simd_cross(SIMD3<Double>(positions[b] - positions[a]), SIMD3<Double>(positions[c] - positions[a]))
            accumulated[a] += normal; accumulated[b] += normal; accumulated[c] += normal
        }
        return accumulated.enumerated().map { index, normal in
            simd_length_squared(normal) > 1e-30 ? SIMD3<Float>(simd_normalize(normal)) : simd_normalize(fallback[index])
        }
    }
}
