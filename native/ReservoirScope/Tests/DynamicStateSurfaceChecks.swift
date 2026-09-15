// Synthetic coordinate fixtures only. No live source or runtime is opened.
import Foundation
import AppKit
import MetalKit
import CryptoKit

@MainActor private struct DynamicStateSurfaceChecks {
    var passed = 0
    var maximumGPUError = 0.0
    mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    func rejects(_ work: () throws -> Void) -> Bool { do { try work(); return false } catch { return true } }
    mutating func run() throws {
        guard CommandLine.arguments.count == 2, let device = MTLCreateSystemDefaultDevice(),
              let queue = device.makeCommandQueue() else { throw SurfaceRenderError("An output directory and Metal device are required.") }
        let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let standard = StateSurfaceAtlas.standard, rebuilt = try StateSurfaceAtlas(nodeCount: 128)
        try check(rebuilt.sites == standard.sites && rebuilt.interpolationWeights == standard.interpolationWeights
            && rebuilt.unitVertices == standard.unitVertices && rebuilt.triangles == standard.triangles
            && rebuilt.layoutVersion == StateSurfaceAtlas.version, "Explicit 128 map exactly preserves the native standard map")
        try check(rejects { _ = try StateSurfaceAtlas(nodeCount: 0) }
            && rejects { _ = try StateSurfaceAtlas(nodeCount: 129) }
            && rejects { _ = try StateSurfaceMath.field(.signedActivation, activations: []) }
            && rejects { _ = try StateSurfaceMath.field(.signedActivation, activations: Array(repeating: 0, count: 129)) },
            "Empty and oversized networks reject before constructing or rendering a map")
        let library = try device.makeLibrary(source: StateSurfaceRenderer.shader, options: nil)
        guard let function = library.makeFunction(name: "surface_dynamic_field_check") else { throw SurfaceRenderError("Dynamic field kernel missing") }
        let pipeline = try device.makeComputePipelineState(function: function)
        for count in [1, 2, 8, 32, 128] {
            let atlas = try StateSurfaceAtlas(nodeCount: count)
            try check(atlas.coordinateCount == count && atlas.sites.count == count
                && atlas.interpolationWeights.count == count * atlas.unitVertices.count,
                "\(count) coordinates have exactly \(count) sites and unpadded interpolation rows")
            let constant = try atlas.interpolate(Array(repeating: 0.37, count: count))
            try check(constant.allSatisfy { abs($0 - 0.37) <= 1e-7 }, "\(count)-coordinate interpolation preserves a constant field")
            let values = atlas.sites.map { Double($0.x) * 0.7 + Double($0.y) * 0.2 }
            let field = try StateSurfaceMath.field(.signedActivation, activations: values)
            try check(field.values == values && field.activations.count == count,
                "\(count)-coordinate field retains every exact input without padding")
            var correctMesh = true
            for fill in [0.0, 68, 100] {
                let mesh = try StateSurfaceMath.mesh(atlas: atlas, field: field, fillPct: fill, relief: 0.2)
                correctMesh = correctMesh && mesh.sitePositions.count == count
                    && abs(mesh.volume - mesh.targetVolume) <= max(1e-12, mesh.targetVolume * 2e-6)
                    && mesh.positions.allSatisfy { simd_length($0) <= 1 + 2e-7 }
                    && mesh.normals.allSatisfy { abs(simd_length($0) - 1) < 2e-7 }
                for index in atlas.sites.indices where fill > 0 {
                    let face = atlas.triangles[atlas.siteTriangleIndices[index]]
                    let a = mesh.positions[Int(face.x)], b = mesh.positions[Int(face.y)], c = mesh.positions[Int(face.z)]
                    correctMesh = correctMesh && abs(simd_dot(mesh.sitePositions[index] - a, simd_normalize(simd_cross(b-a,c-a)))) < 2e-7
                        && simd_length(simd_cross(mesh.sitePositions[index], atlas.sites[index])) < 2e-7
                }
            }
            try check(correctMesh, "\(count)-coordinate meshes preserve volume, containment, normals and exact marker intersections")
            let implicit = try StateSurfaceMath.mesh(field: field, fillPct: 68, relief: 0.2)
            let explicit = try StateSurfaceMath.mesh(atlas: atlas, field: field, fillPct: 68, relief: 0.2)
            try check(implicit.positions == explicit.positions && implicit.sitePositions == explicit.sitePositions,
                "\(count)-coordinate default mesh infers the same explicit drawing map")
            var impulse = Array(repeating: 0.0, count: count); impulse[count-1] = 1
            for (name, coordinates) in [("signed", values), ("last-node impulse", impulse)] {
                let floats = coordinates.map(Float.init)
                guard let weights = atlas.interpolationWeights.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }),
                      let input = floats.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }),
                      let buffer = device.makeBuffer(length: atlas.unitVertices.count * 4, options: .storageModeShared),
                      let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw SurfaceRenderError("GPU check allocation failed") }
                var vertexCount = UInt32(atlas.unitVertices.count), nodes = UInt32(count)
                encoder.setComputePipelineState(pipeline)
                encoder.setBuffer(weights, offset: 0, index: 0); encoder.setBuffer(input, offset: 0, index: 1)
                encoder.setBuffer(buffer, offset: 0, index: 2)
                encoder.setBytes(&vertexCount, length: 4, index: 3); encoder.setBytes(&nodes, length: 4, index: 4)
                encoder.dispatchThreads(MTLSize(width: Int(vertexCount),height: 1,depth: 1),
                    threadsPerThreadgroup: MTLSize(width: min(128,pipeline.maxTotalThreadsPerThreadgroup),height: 1,depth: 1))
                encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
                guard command.status == .completed else { throw SurfaceRenderError(command.error?.localizedDescription ?? "GPU check failed") }
                let cpu = try atlas.interpolate(coordinates), gpu = buffer.contents().bindMemory(to: Float.self, capacity: cpu.count)
                let error = cpu.indices.map { abs(Double(cpu[$0]) - Double(gpu[$0])) }.max() ?? .infinity
                maximumGPUError = max(maximumGPUError, error)
                try check(cpu.indices.allSatisfy { gpu[$0].isFinite } && error <= 3e-6,
                    "\(count)-coordinate GPU \(name) field agrees with CPU within 3e-6")
            }
        }
        let smallAtlas = try StateSurfaceAtlas(nodeCount: 32)
        try check(rejects { _ = try StateSurfaceMath.mesh(atlas: smallAtlas, values: Array(repeating: 0.0,count: 128),scale: -1...1,fillPct: 68) },
            "An explicit 32-coordinate atlas rejects 128 values")
        let renderer = try StateSurfaceRenderer(device: device)
        let targets = try DynamicSurfaceTargets(device: device)
        var imageHashes: [String:String] = [:], first32: Data?
        for count in [32, 128, 1, 32] {
            let atlas = try StateSurfaceAtlas(nodeCount: count)
            let values = atlas.sites.map { Double($0.x) * 0.7 + Double($0.y) * 0.2 }
            var input = StateSurfaceRenderInput(values: values,lower: -1,upper: 1,fillPct: 68,relief: 0.2,
                cutaway: false,selectedNode: count-1,showSites: true,flatLighting: true)
            try renderer.update(input)
            let image = try targets.render(renderer)
            try check(renderer.nodeCount == count && renderer.mesh?.sitePositions.count == count,
                "Renderer switches atomically to exactly \(count) coordinates")
            try check(renderer.pick(point: CGPoint(x: 192,y: 192),size: CGSize(width: 384,height: 384)).map { (0..<count).contains($0) } == true,
                "\(count)-coordinate picking returns an actual coordinate index")
            let markers = renderer.vertexCount
            input.showSites = false; try renderer.update(input)
            let unmarked = try targets.render(renderer)
            try check(markers-renderer.vertexCount == count && unmarked != image,
                "Exactly\(count) exact-node markers are submitted and visibly alter the frame")
            input.showSites = true; input.selectedNode = count
            try check(rejects { _ = try renderer.update(input) } && renderer.nodeCount == count,
                "Selection outside the actual \(count)-coordinate range rejects without replacing the accepted map")
            let name = "surface-\(count).png"
            if count == 32, let first32 { try check(image == first32, "Returning from 128 and 1 to 32 restores identical pixels") }
            else {
                if count == 32 { first32 = image }
                let png = try targets.png(image)
                try png.write(to: output.appendingPathComponent(name), options: .atomic)
                imageHashes[name] = SHA256.hash(data: png).map { String(format:"%02x",$0) }.joined()
            }
        }
        let report: [String:Any] = ["checks":passed,"maximum_gpu_error":maximumGPUError,"device":device.name,
            "tested_node_counts":[1,2,8,32,128],"image_sha256":imageHashes,"scope":"synthetic offscreen correctness; no live files or displayed FPS measurement"]
        try JSONSerialization.data(withJSONObject: report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("checks.json"),options:.atomic)
        print("\(passed) dynamic-coordinate checks passed; images: \(output.path); max GPU error: \(maximumGPUError)")
    }
}

@MainActor private struct DynamicSurfaceTargets {
    let pass: MTLRenderPassDescriptor
    let color: MTLTexture
    let readback: MTLBuffer
    let width = 384
    init(device: MTLDevice) throws {
        func texture(_ format: MTLPixelFormat) throws -> MTLTexture {
            let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat:format,width:384,height:384,mipmapped:false)
            descriptor.storageMode = .private; descriptor.usage = .renderTarget
            guard let result = device.makeTexture(descriptor:descriptor) else { throw SurfaceRenderError("No offscreen texture") }
            return result
        }
        color = try texture(.bgra8Unorm_srgb)
        guard let buffer = device.makeBuffer(length:384*384*4,options:.storageModeShared) else { throw SurfaceRenderError("No image readback") }
        readback = buffer
        pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = color; pass.colorAttachments[0].loadAction = .clear; pass.colorAttachments[0].storeAction = .store
        pass.colorAttachments[0].clearColor = MTLClearColor(red:0.009,green:0.017,blue:0.031,alpha:1)
        pass.depthAttachment.texture = try texture(.depth32Float); pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.clearDepth = 1; pass.depthAttachment.storeAction = .dontCare
    }
    func render(_ renderer: StateSurfaceRenderer) throws -> Data {
        guard let command = renderer.queue.makeCommandBuffer(),
              renderer.encode(command:command,pass:pass,size:CGSize(width:width,height:width)),
              let encoder = command.makeBlitCommandEncoder() else { throw SurfaceRenderError("No offscreen render encoder") }
        encoder.copy(from:color,sourceSlice:0,sourceLevel:0,sourceOrigin:MTLOrigin(x:0,y:0,z:0),
            sourceSize:MTLSize(width:width,height:width,depth:1),to:readback,destinationOffset:0,destinationBytesPerRow:width*4,destinationBytesPerImage:width*width*4)
        encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
        guard command.status == .completed else { throw SurfaceRenderError(command.error?.localizedDescription ?? "Offscreen render failed") }
        return Data(bytes:readback.contents(),count:readback.length)
    }
    func png(_ bgra: Data) throws -> Data {
        guard let bitmap = NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:width,pixelsHigh:width,bitsPerSample:8,samplesPerPixel:4,
            hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:width*4,bitsPerPixel:32), let rgba = bitmap.bitmapData else {
            throw SurfaceRenderError("No PNG bitmap")
        }
        for index in stride(from:0,to:bgra.count,by:4) {
            rgba[index] = bgra[index+2]; rgba[index+1] = bgra[index+1]; rgba[index+2] = bgra[index]; rgba[index+3] = bgra[index+3]
        }
        guard let data = bitmap.representation(using:.png,properties:[:]) else { throw SurfaceRenderError("PNG encoding failed") }
        return data
    }
}

Task { @MainActor in
    do { var checks = DynamicStateSurfaceChecks(); try checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
