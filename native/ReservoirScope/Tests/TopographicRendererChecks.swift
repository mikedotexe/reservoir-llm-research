import Foundation
import MetalKit
import CryptoKit
import ImageIO
import UniformTypeIdentifiers

/// Deterministic offscreen checks use actual production shaders/mesh/picking.
/// TOPOGRAPHY_BASELINE compiles this same fixture writer against pristine legacy
/// sources, before the topography API existed; no modern path is executed there.
@MainActor
private struct TopographicRendererChecks {
    private var passed = 0
    private var renderedFrames = 0
    private var computeFrames = 0
    private var maximumGPUFieldError = 0.0
    private var fixtures: [[String: Any]] = []
    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    mutating func run() throws {
        guard CommandLine.arguments.count >= 3 else { throw SurfaceRenderError("Expected resources and output directory.") }
        let resources = URL(fileURLWithPath: CommandLine.arguments[1])
        let output = URL(fileURLWithPath: CommandLine.arguments[2])
        let baseline = CommandLine.arguments.count > 3 ? URL(fileURLWithPath: CommandLine.arguments[3]) : nil
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        guard let device = MTLCreateSystemDefaultDevice() else { throw SurfaceRenderError("Metal unavailable.") }
        let renderer = try StateSurfaceRenderer(device: device, sampleCount: 1)
        let targets = try TopographicTargets(device: device)
        struct Stage: Decodable { struct Frame: Decodable { let state: [Double] }; let frames: [Frame] }
        let stageURL = resources.appendingPathComponent("essentials-stage-1.json")
        let stage = try JSONDecoder().decode(Stage.self, from: Data(contentsOf: stageURL))
        guard stage.frames.count >= 30, stage.frames[11].state.count == 32 else { throw SurfaceRenderError("Bundled Stage 1 observations unavailable.") }
        let evidence = try EvidenceStore.load(historicalURL: resources.appendingPathComponent("data.json"),
            geometryURL: resources.appendingPathComponent("state-geometry.json"))
        guard let retained = evidence.stateReplay, retained.frames.count >= 512 else { throw SurfaceRenderError("Retained native128 replay unavailable.") }
        var opposed = Array(repeating: 0.0, count: 32); opposed[7] = 0.8; opposed[23] = -0.8
        let cases: [(String, [Double], String)] = [
            ("32-zero", Array(repeating: 0, count: 32), "Synthetic zero coordinates"),
            ("32-positive", Array(repeating: 0.6, count: 32), "Synthetic uniform +0.6 coordinates"),
            ("32-negative", Array(repeating: -0.6, count: 32), "Synthetic uniform -0.6 coordinates"),
            ("32-opposed", opposed, "Synthetic opposed coordinates: 7=+0.8, 23=-0.8, others zero"),
            ("32-stage1-step1", stage.frames[0].state, "Bundled Essentials Stage 1 exact step 1 state; focal screenshot reference"),
            ("32-stage1-step12", stage.frames[11].state, "Bundled Essentials Stage 1 exact step 12 state"),
            ("128-retained-row0", retained.frames[0].activations, "Retained native128 exact row 0; no paired fill, 68% preview only")
        ]
        func input(_ values: [Double], topographic: Bool, relief: Double = 0.16, fill: Double? = nil,
                   cutaway: Bool = false, sites: Bool = true) -> StateSurfaceRenderInput {
            var result = StateSurfaceRenderInput(values: values, lower: -1, upper: 1,
                fillPct: fill ?? (values.count == 32 ? 100 : 68), relief: relief, cutaway: cutaway,
                selectedNode: 0, showSites: sites, flatLighting: false)
            #if !TOPOGRAPHY_BASELINE
            result.presentation = topographic ? .topography : .surface
            #endif
            return result
        }
        func pixels() throws -> Data {
            guard let command = renderer.queue.makeCommandBuffer(),
                  renderer.encode(command: command, pass: targets.pass, size: targets.size),
                  let blit = command.makeBlitCommandEncoder() else { throw SurfaceRenderError("No offscreen command encoder.") }
            blit.copy(from: targets.color, sourceSlice: 0, sourceLevel: 0, sourceOrigin: MTLOrigin(x: 0, y: 0, z: 0),
                sourceSize: MTLSize(width: targets.edge, height: targets.edge, depth: 1), to: targets.readback,
                destinationOffset: 0, destinationBytesPerRow: targets.edge * 4, destinationBytesPerImage: targets.edge * targets.edge * 4)
            blit.endEncoding(); command.commit(); command.waitUntilCompleted()
            guard command.status == .completed else { throw SurfaceRenderError(command.error?.localizedDescription ?? "GPU command failed.") }
            return Data(bytes: targets.readback.contents(), count: targets.readback.length)
        }
        func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
        for (name, values, provenance) in cases {
            try renderer.update(input(values, topographic: false))
            let bytes = try pixels(); renderedFrames += 1
            let label = "legacy-" + name
            try bytes.write(to: output.appendingPathComponent(label + ".bgra"))
            try targets.writePNG(bytes, to: output.appendingPathComponent(label + ".png"))
            var entry: [String: Any] = ["name": label, "pixel_sha256": sha(bytes), "coordinate_count": values.count,
                "provenance": provenance, "values": values, "mode": "surface", "fill_interpretation": values.count == 32 ? "100% fixed display size, reproducing the previous Essentials call" : "68% unpaired preview"]
            #if !TOPOGRAPHY_BASELINE
            if let baseline {
                let previous = try Data(contentsOf: baseline.appendingPathComponent(label + ".bgra"))
                try check(bytes == previous, "Legacy \(name) pixels remain byte-identical to the pristine renderer")
                entry["pristine_pixel_match"] = true
            }
            #endif
            fixtures.append(entry)
        }
        #if !TOPOGRAPHY_BASELINE
        let library = try device.makeLibrary(source: StateSurfaceRenderer.shader, options: nil)
        guard let function = library.makeFunction(name: "surface_dynamic_field_check") else { throw SurfaceRenderError("No dynamic field-check kernel.") }
        let computePipeline = try device.makeComputePipelineState(function: function)
        func denseFieldError(_ values: [Double]) throws -> Double {
            let atlas = try StateSurfaceAtlas(nodeCount: values.count, rows: 64, columns: 128)
            let input = values.map(Float.init)
            guard let weights = atlas.interpolationWeights.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }),
                  let valueBuffer = input.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }),
                  let output = device.makeBuffer(length: atlas.unitVertices.count * MemoryLayout<Float>.stride, options: .storageModeShared),
                  let command = renderer.queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw SurfaceRenderError("No dense field compute resources.") }
            var count = UInt32(atlas.unitVertices.count), nodes = UInt32(values.count)
            encoder.setComputePipelineState(computePipeline)
            encoder.setBuffer(weights, offset: 0, index: 0); encoder.setBuffer(valueBuffer, offset: 0, index: 1)
            encoder.setBuffer(output, offset: 0, index: 2)
            encoder.setBytes(&count, length: MemoryLayout<UInt32>.stride, index: 3)
            encoder.setBytes(&nodes, length: MemoryLayout<UInt32>.stride, index: 4)
            encoder.dispatchThreads(MTLSize(width: Int(count), height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: min(128, computePipeline.maxTotalThreadsPerThreadgroup), height: 1, depth: 1))
            encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
            guard command.status == .completed else { throw SurfaceRenderError("Dense field GPU computation failed.") }
            let gpu = output.contents().bindMemory(to: Float.self, capacity: Int(count))
            let cpu = try atlas.interpolate(values)
            guard cpu.indices.allSatisfy({ gpu[$0].isFinite }) else { return .infinity }
            return cpu.indices.map { abs(Double(gpu[$0]) - Double(cpu[$0])) }.max() ?? .infinity
        }
        for (name, values, provenance) in cases {
            let gpuError = try denseFieldError(values)
            computeFrames += 1; maximumGPUFieldError = max(maximumGPUFieldError, gpuError)
            try check(gpuError <= 3e-6, "Dense GPU field matches CPU interpolation within 3e-6 for \(name)")
            try renderer.update(input(values, topographic: true))
            let bytes = try pixels(); renderedFrames += 1
            guard let mesh = renderer.mesh else { throw SurfaceRenderError("Topographic mesh unavailable.") }
            try check(renderer.nodeCount == values.count && mesh.sitePositions.count == values.count && mesh.fieldValues.count == mesh.positions.count,
                "Topographic \(name) retains exactly \(values.count) mapped coordinates")
            try check(mesh.normals.count == mesh.positions.count && mesh.positions.allSatisfy { simd_length($0).isFinite }
                && mesh.normals.allSatisfy { abs(simd_length($0) - 1) < 1e-4 },
                "Topographic \(name) has finite geometry and unit surface normals")
            if name == "32-zero" || name == "32-positive" || name == "32-negative" {
                let expected = 0.82 + 0.16 * values[0]
                let radialError = mesh.positions.map { abs(Double(simd_length($0)) - expected) }.max() ?? .infinity
                try check(radialError < 3e-6, "\(name) radius follows fixed 0.82 + gain × signed field")
            }
            let label = "topography-" + name
            try bytes.write(to: output.appendingPathComponent(label + ".bgra"))
            try targets.writePNG(bytes, to: output.appendingPathComponent(label + ".png"))
            fixtures.append(["name": label, "pixel_sha256": sha(bytes), "coordinate_count": values.count,
                "provenance": provenance, "values": values, "mode": "topography", "display_reference_radius": 0.82,
                "requested_gain": 0.16, "applied_gain": mesh.appliedRelief, "mesh_vertex_count": mesh.positions.count,
                "minimum_radius": mesh.positions.map { Double(simd_length($0)) }.min()!,
                "maximum_radius": mesh.positions.map { Double(simd_length($0)) }.max()!])
        }
        let observed = stage.frames[0].state
        let primary = input(observed, topographic: true)
        try renderer.update(primary)
        let original = try pixels(); renderedFrames += 1
        let positions = renderer.mesh!.positions, count = renderer.vertexCount, memory = renderer.bufferBytes
        try check(try !renderer.update(primary) && renderer.vertexCount == count && renderer.bufferBytes == memory,
            "Duplicate topographic observations retain immutable resources")
        let repeated = try pixels(); renderedFrames += 1
        try check(original == repeated, "Repeated rendering has no time-driven state or geometry movement")
        try renderer.update(input(stage.frames[29].state, topographic: true))
        let changed = try pixels(); renderedFrames += 1
        try check(changed != original, "A different saved reservoir state changes topographic pixels")
        try renderer.update(primary)
        let replayed = try pixels(); renderedFrames += 1
        try check(replayed == original && renderer.mesh!.positions == positions,
            "Rewinding A → B → A restores exact geometry and pixels without temporal easing")
        try renderer.update(input(observed, topographic: true, relief: 0))
        let flat = try pixels(); renderedFrames += 1
        try targets.writePNG(flat, to: output.appendingPathComponent("topography-32-stage1-gain-zero.png"))
        try check(flat != original && renderer.mesh!.positions.allSatisfy { abs(Double(simd_length($0)) - 0.82) < 3e-6 },
            "Zero height gain makes a sphere while nonzero gain changes actual geometry and pixels")
        try renderer.update(input(observed, topographic: true, fill: 0))
        let dummyZeroFill = try pixels(); renderedFrames += 1
        try check(renderer.mesh!.positions == positions && dummyZeroFill == original,
            "Topographic geometry and exact markers do not depend on dummy display fill")
        let center = CGPoint(x: targets.edge / 2, y: targets.edge / 2)
        try check(renderer.pick(point: center, size: targets.size).map { (0..<32).contains($0) } == true
            && renderer.pick(point: .zero, size: targets.size) == nil,
            "Topographic surface picking returns a real coordinate; background returns none")
        let fullCount = renderer.vertexCount
        try renderer.update(input(observed, topographic: true, cutaway: true))
        let cut = try pixels(); renderedFrames += 1
        try targets.writePNG(cut, to: output.appendingPathComponent("topography-32-stage1-cutaway.png"))
        try check(cut != original && renderer.vertexCount < fullCount && renderer.mesh!.positions == positions,
            "Cutaway removes the front display triangles without changing the recorded full surface")
        try check(renderer.pick(point: center, size: targets.size) == nil,
            "The opaque unmeasured cut face blocks picks through to hidden coordinates")
        try renderer.update(input(observed, topographic: true, sites: false))
        let withoutSites = try pixels(); renderedFrames += 1
        try check(renderer.vertexCount + 32 == fullCount && withoutSites != original,
            "Hiding sites removes exactly 32 markers and leaves the interpolated surface intact")
        try renderer.update(input(retained.frames[0].activations, topographic: false))
        let switchedLegacy = try pixels(); renderedFrames += 1
        let legacySaved = try Data(contentsOf: output.appendingPathComponent("legacy-128-retained-row0.bgra"))
        try check(renderer.nodeCount == 128 && switchedLegacy == legacySaved,
            "Switching 32-node topography back to native128 restores the same legacy pixels")
        renderer.clear()
        try check(renderer.mesh == nil && renderer.vertexCount == 0 && renderer.pick(point: center, size: targets.size) == nil,
            "Clearing an unavailable observation removes old geometry and picking")
        #endif
        let receipt: [String: Any] = ["schema": "reservoir.topographic_renderer_checks.v1", "device": device.name,
            "passed_checks": passed, "rendered_frames": renderedFrames, "compute_frames": computeFrames, "maximum_gpu_field_error": maximumGPUFieldError, "edge_pixels": targets.edge, "sample_count": 1,
            "fixtures": fixtures, "stage1_sha256": sha(try Data(contentsOf: stageURL)),
            "retained_binary_sha256": sha(try Data(contentsOf: resources.appendingPathComponent("state-replay.bin"))),
            "scope": "Deterministic offscreen rendering and picking only; no presented-window performance or live system observations."]
        try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("receipt.json"))
        print("\(passed) topographic renderer checks passed; \(renderedFrames) deterministic offscreen frames on \(device.name).")
    }
}

private struct TopographicTargets {
    let edge = 768
    var size: CGSize { CGSize(width: edge, height: edge) }
    let pass: MTLRenderPassDescriptor
    let color: MTLTexture
    let readback: MTLBuffer
    init(device: MTLDevice) throws {
        func texture(_ format: MTLPixelFormat) throws -> MTLTexture {
            let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: format, width: 768, height: 768, mipmapped: false)
            descriptor.storageMode = .private; descriptor.usage = .renderTarget
            guard let value = device.makeTexture(descriptor: descriptor) else { throw SurfaceRenderError("No check render texture.") }
            return value
        }
        color = try texture(.bgra8Unorm_srgb)
        guard let buffer = device.makeBuffer(length: 768 * 768 * 4, options: .storageModeShared) else { throw SurfaceRenderError("No check readback buffer.") }
        readback = buffer
        pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = color; pass.colorAttachments[0].loadAction = .clear; pass.colorAttachments[0].storeAction = .store
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        pass.depthAttachment.texture = try texture(.depth32Float); pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.clearDepth = 1; pass.depthAttachment.storeAction = .dontCare
    }
    func writePNG(_ bgra: Data, to url: URL) throws {
        let info = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedFirst.rawValue).union(.byteOrder32Little)
        guard let provider = CGDataProvider(data: bgra as CFData),
              let image = CGImage(width: edge, height: edge, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: edge * 4,
                space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: info, provider: provider,
                decode: nil, shouldInterpolate: false, intent: .defaultIntent),
              let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw SurfaceRenderError("Could not create check PNG.")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw SurfaceRenderError("Could not write check PNG.") }
    }
}
Task { @MainActor in
    do { var checks = TopographicRendererChecks(); try checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
