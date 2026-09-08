import Foundation
import MetalKit
import CryptoKit

@MainActor
private struct StateSurfaceRendererChecks {
    private var passed = 0
    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    mutating func run() throws {
        guard CommandLine.arguments.count == 2 else { throw SurfaceRenderError("Use check-state-surface-renderer.sh") }
        let resources = URL(fileURLWithPath: CommandLine.arguments[1])
        let evidence = try EvidenceStore.load(historicalURL: resources.appendingPathComponent("data.json"),
                                              geometryURL: resources.appendingPathComponent("state-geometry.json"))
        guard let replay = evidence.stateReplay, let device = MTLCreateSystemDefaultDevice(),
              let queue = device.makeCommandQueue() else { throw SurfaceRenderError("Retained replay or Metal unavailable") }
        let atlas = StateSurfaceAtlas.standard
        let library = try device.makeLibrary(source: StateSurfaceRenderer.shader, options: nil)
        guard let function = library.makeFunction(name: "surface_field_check") else { throw SurfaceRenderError("Missing renderer field-check kernel") }
        let pipeline = try device.makeComputePipelineState(function: function)
        guard let weights = atlas.interpolationWeights.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }) else {
            throw SurfaceRenderError("No shared weight buffer")
        }
        var one = Array(repeating: 0.0, count: 128); one[31] = 1
        var opposed = Array(repeating: 0.0, count: 128); opposed[31] = 1; opposed[94] = -1
        var fields = [("zero", Array(repeating: 0.0, count: 128)), ("constant", Array(repeating: 0.37, count: 128)),
                      ("one coordinate", one), ("opposed coordinates", opposed)]
        for index in [0, 1, 127, 255, 511, 767, 1023] { fields.append(("retained row \(index)", replay.frames[index].activations)) }
        var maxGPUError = 0.0
        var computeFrames = 0
        for (name, values) in fields {
            let floats = values.map(Float.init)
            guard let input = floats.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }),
                  let output = device.makeBuffer(length: atlas.unitVertices.count * MemoryLayout<Float>.stride, options: .storageModeShared),
                  let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else {
                throw SurfaceRenderError("No field-check compute resources")
            }
            var count = UInt32(atlas.unitVertices.count)
            encoder.setComputePipelineState(pipeline)
            encoder.setBuffer(weights, offset: 0, index: 0); encoder.setBuffer(input, offset: 0, index: 1)
            encoder.setBuffer(output, offset: 0, index: 2); encoder.setBytes(&count, length: MemoryLayout<UInt32>.stride, index: 3)
            encoder.dispatchThreads(MTLSize(width: Int(count), height: 1, depth: 1),
                                    threadsPerThreadgroup: MTLSize(width: min(128, pipeline.maxTotalThreadsPerThreadgroup), height: 1, depth: 1))
            encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
            guard command.status == .completed else { throw SurfaceRenderError(command.error?.localizedDescription ?? "GPU field-check command failed") }
            computeFrames += 1
            let gpu = output.contents().bindMemory(to: Float.self, capacity: Int(count))
            let cpu = try atlas.interpolate(values)
            let error = cpu.indices.map { abs(Double(cpu[$0]) - Double(gpu[$0])) }.max()!
            maxGPUError = max(maxGPUError, error)
            try check(cpu.indices.allSatisfy { gpu[$0].isFinite } && error <= 3e-6,
                      "GPU field matches CPU atlas within 3e-6 for \(name)")
        }

        let renderer = try StateSurfaceRenderer(device: device, sampleCount: 1)
        let targets = try SurfaceCheckTargets(device: device)
        var renderedFrames = 0
        func render() throws -> Data {
            guard let command = renderer.queue.makeCommandBuffer() else { throw SurfaceRenderError("No render check command") }
            guard renderer.encode(command: command, pass: targets.pass, size: CGSize(width: 256, height: 256)),
                  let blit = command.makeBlitCommandEncoder() else { throw SurfaceRenderError("Offscreen render was not encoded") }
            blit.copy(from: targets.color, sourceSlice: 0, sourceLevel: 0, sourceOrigin: MTLOrigin(x: 0,y: 0,z: 0),
                      sourceSize: MTLSize(width: 256,height: 256,depth: 1), to: targets.readback,
                      destinationOffset: 0, destinationBytesPerRow: 1024, destinationBytesPerImage: 256*1024)
            blit.endEncoding(); command.commit(); command.waitUntilCompleted()
            guard command.status == .completed else { throw SurfaceRenderError(command.error?.localizedDescription ?? "Offscreen render failed") }
            renderedFrames += 1
            return Data(bytes: targets.readback.contents(), count: targets.readback.length)
        }
        var input = StateSurfaceRenderInput(values: replay.frames[0].activations, lower: -1, upper: 1,
            fillPct: 68, relief: 0, cutaway: false, selectedNode: 0)
        try check(try renderer.update(input), "First retained vector creates a surface observation")
        let bufferBytes = renderer.bufferBytes
        try check(try !renderer.update(input) && renderer.bufferBytes == bufferBytes && renderer.submittedFrames == 0,
                  "Duplicate observation preserves resources and invents no native draw submission")
        let color = try render(), repeated = try render()
        try check(color == repeated, "The same observation renders identical pixels without time-driven movement")
        try check(renderer.vertexCount > atlas.triangles.count * 3 && bufferBytes > atlas.interpolationWeights.count * 4,
                  "Surface triangles, reference geometry and exact sites use allocated GPU resources")
        try check(renderer.pick(point: CGPoint(x: 128,y: 128), size: CGSize(width: 256,height: 256)).map { (0..<128).contains($0) } == true
            && renderer.pick(point: CGPoint(x: 0,y: 0), size: CGSize(width: 256,height: 256)) == nil,
                  "A center surface hit selects a mapped coordinate; background clicks select none")
        input.values = replay.frames[511].activations; try renderer.update(input)
        let differentState = try render()
        try check(color != differentState, "Different accepted retained states change the rendered surface colors")
        input.values = replay.frames[0].activations; input.relief = 0.14; try renderer.update(input)
        let relief = try render()
        guard let mesh = renderer.mesh else { throw SurfaceRenderError("Relief mesh missing") }
        try check(relief != color && mesh.appliedRelief > 0 && abs(mesh.volume-mesh.targetVolume) <= mesh.targetVolume * 2e-6,
                  "Actual relief changes pixels while preserving the declared preview volume")
        let fullVertexCount = renderer.vertexCount
        input.cutaway = true; try renderer.update(input)
        let cut = try render()
        try check(cut != relief && renderer.vertexCount < fullVertexCount && renderer.mesh?.volume == mesh.volume,
                  "Cutaway changes rendered geometry while retaining the same complete-mesh volume check")
        try check(renderer.pick(point: CGPoint(x: 128,y: 128), size: CGSize(width: 256,height: 256)) == nil,
                  "Clicking the opaque unmeasured cut face does not select a hidden back-surface coordinate")
        renderer.clear()
        let empty = try render()
        try check(renderer.mesh == nil && renderer.vertexCount == 0 && renderer.pick(point: CGPoint(x: 128,y: 128), size: CGSize(width: 256,height: 256)) == nil
            && empty != cut, "Clearing invalid/unavailable evidence removes old geometry and picking")
        try check(computeFrames == 11 && renderedFrames == 6 && renderer.submittedFrames == 0,
                  "Finite checks completed 11 GPU field commands and 6 offscreen frames without a presented window")
        print("\(passed) state-surface renderer checks passed. Device: \(device.name). Maximum GPU field error: \(maxGPUError). Correctness fixtures only; no profiling timings or live-system reads.")
    }
}

private struct SurfaceCheckTargets {
    let pass: MTLRenderPassDescriptor
    let color: MTLTexture
    let readback: MTLBuffer
    init(device: MTLDevice) throws {
        func texture(_ format: MTLPixelFormat) throws -> MTLTexture {
            let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: format, width: 256, height: 256, mipmapped: false)
            d.storageMode = .private; d.usage = .renderTarget
            guard let texture = device.makeTexture(descriptor: d) else { throw SurfaceRenderError("Could not allocate check texture") }
            return texture
        }
        color = try texture(.bgra8Unorm_srgb)
        guard let readback = device.makeBuffer(length: 256*256*4, options: .storageModeShared) else { throw SurfaceRenderError("Could not allocate check readback") }
        self.readback = readback
        let pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = color; pass.colorAttachments[0].loadAction = .clear; pass.colorAttachments[0].storeAction = .store
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0.009,green: 0.017,blue: 0.031,alpha: 1)
        pass.depthAttachment.texture = try texture(.depth32Float); pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.clearDepth = 1; pass.depthAttachment.storeAction = .dontCare
        self.pass = pass
    }
}

Task { @MainActor in
    do { var checks = StateSurfaceRendererChecks(); try checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
