import SwiftUI
import MetalKit
import simd

struct StateSurfaceRenderInput: Equatable {
    var values: [Double]
    var lower: Double
    var upper: Double
    var fillPct: Double
    var relief: Double
    var cutaway: Bool
    var selectedNode: Int
    var showSites = true
    var flatLighting = false
}

struct StateSurfaceMetrics: Equatable {
    var appliedRelief: Double
    var volumeError: Double
    var fallback: String?
    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.appliedRelief == rhs.appliedRelief && lhs.fallback == rhs.fallback &&
        (lhs.volumeError == rhs.volumeError || (lhs.volumeError.isNaN && rhs.volumeError.isNaN))
    }
}

struct StateSurfaceScene: NSViewRepresentable {
    var input: StateSurfaceRenderInput
    var accessibilitySubject = "Native reservoir"
    var onSelect: (Int) -> Void
    var onMetrics: (StateSurfaceMetrics) -> Void
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeNSView(context: Context) -> StateSurfaceMetalView {
        let view = StateSurfaceMetalView(frame: .zero, device: MTLCreateSystemDefaultDevice())
        view.colorPixelFormat = .bgra8Unorm_srgb
        view.depthStencilPixelFormat = .depth32Float
        view.sampleCount = view.device?.supportsTextureSampleCount(4) == true ? 4 : 1
        view.clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        view.isPaused = true; view.enableSetNeedsDisplay = true
        do {
            guard let device = view.device else { throw SurfaceRenderError("No Metal device is available.") }
            let renderer = try StateSurfaceRenderer(device: device, sampleCount: view.sampleCount)
            context.coordinator.renderer = renderer
            view.renderer = renderer; renderer.view = view; view.delegate = renderer
        } catch {
            let label = NSTextField(wrappingLabelWithString: error.localizedDescription)
            label.frame = NSRect(x: 20, y: 20, width: 500, height: 70); view.addSubview(label)
        }
        return view
    }
    func updateNSView(_ view: StateSurfaceMetalView, context: Context) {
        view.onSelect = onSelect
        do {
            if try context.coordinator.renderer?.update(input) == true,
               let mesh = context.coordinator.renderer?.mesh {
                let metrics = StateSurfaceMetrics(appliedRelief: mesh.appliedRelief,
                    volumeError: abs(mesh.volume - mesh.targetVolume), fallback: mesh.fallbackReason)
                DispatchQueue.main.async { onMetrics(metrics) }
            }
        } catch {
            // Clear a previous observation rather than present it as this input.
            context.coordinator.renderer?.clear()
            let metrics = StateSurfaceMetrics(appliedRelief: 0, volumeError: .nan, fallback: error.localizedDescription)
            DispatchQueue.main.async { onMetrics(metrics) }
        }
        view.setAccessibilityLabel("\(accessibilitySubject) state surface. Fixed coordinate map. Drag to orbit; click a surface patch to inspect its nearest mapped coordinate. Arrow keys orbit, Space resets. Values and geometry use accepted observations without temporal easing.")
    }
    static func dismantleNSView(_ view: StateSurfaceMetalView, coordinator: Coordinator) {
        view.delegate = nil; view.renderer = nil; coordinator.renderer = nil
    }
    final class Coordinator { var renderer: StateSurfaceRenderer? }
}

final class StateSurfaceMetalView: MTKView {
    weak var renderer: StateSurfaceRenderer?
    var onSelect: ((Int) -> Void)?
    private var dragged = false
    override var acceptsFirstResponder: Bool { true }
    override func mouseDown(with event: NSEvent) { window?.makeFirstResponder(self); dragged = false }
    override func mouseDragged(with event: NSEvent) {
        dragged = true; renderer?.orbit(dx: Float(event.deltaX), dy: Float(event.deltaY))
    }
    override func mouseUp(with event: NSEvent) {
        if event.clickCount == 2 { renderer?.resetCamera(); return }
        guard !dragged else { return }
        let point = convert(event.locationInWindow, from: nil)
        if let index = renderer?.pick(point: CGPoint(x: point.x, y: bounds.height - point.y), size: bounds.size) { onSelect?(index) }
    }
    override func scrollWheel(with event: NSEvent) { renderer?.zoom(delta: Float(event.scrollingDeltaY)) }
    override func magnify(with event: NSEvent) { renderer?.zoom(delta: Float(event.magnification) * 180) }
    override func keyDown(with event: NSEvent) {
        switch event.keyCode {
        case 123: renderer?.orbit(dx: -12, dy: 0)
        case 124: renderer?.orbit(dx: 12, dy: 0)
        case 125: renderer?.orbit(dx: 0, dy: 12)
        case 126: renderer?.orbit(dx: 0, dy: -12)
        case 49: renderer?.resetCamera()
        default: super.keyDown(with: event)
        }
    }
}

struct SurfaceRenderError: LocalizedError {
    var message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

private struct SurfaceVertex {
    var position: SIMD4<Float>
    var normal: SIMD4<Float>
    // x = mesh/site index; y = surface(0), reference(1), exact site(2), cap(3);
    // z = reference color code; w = selected marker.
    var info: SIMD4<Float>
    init(_ p: SIMD3<Float>, _ n: SIMD3<Float>, _ info: SIMD4<Float>) {
        position = SIMD4(p, 1); normal = SIMD4(n, 0); self.info = info
    }
}
private struct SurfaceUniforms {
    var mvp: simd_float4x4
    var model: simd_float4x4
    var scale: SIMD4<Float>
}
private struct SurfaceDraw {
    var buffer: MTLBuffer
    var count: Int
    var primitive: MTLPrimitiveType
    var reference = false
}

/// CPU validates the actual relief mesh at observation changes. Metal evaluates
/// the 128-coordinate field and lighting from immutable shared resources.
@MainActor final class StateSurfaceRenderer: NSObject, MTKViewDelegate {
    weak var view: MTKView?
    let device: MTLDevice
    let queue: MTLCommandQueue
    private let pipeline: MTLRenderPipelineState
    private let depth: MTLDepthStencilState
    private let ghostDepth: MTLDepthStencilState
    private let weights: MTLBuffer
    private let atlas = StateSurfaceAtlas.standard
    private var nodeBuffer: MTLBuffer?
    private var draws: [SurfaceDraw] = []
    private var current: StateSurfaceRenderInput?
    private(set) var mesh: StateSurfaceMesh?
    private var yaw: Float = -0.42, pitch: Float = 0.16, distance: Float = 3.5
    private(set) var submittedFrames = 0
    private(set) var lastSubmitCPUms = 0.0
    var bufferBytes: Int { weights.length + (nodeBuffer?.length ?? 0) + draws.reduce(0) { $0 + $1.buffer.length } }
    var vertexCount: Int { draws.reduce(0) { $0 + $1.count } }

    init(device: MTLDevice, sampleCount: Int = 1) throws {
        self.device = device
        guard let queue = device.makeCommandQueue() else { throw SurfaceRenderError("No Metal command queue.") }
        self.queue = queue
        let library = try device.makeLibrary(source: Self.shader, options: nil)
        let descriptor = MTLRenderPipelineDescriptor()
        descriptor.vertexFunction = library.makeFunction(name: "surface_vertex")
        descriptor.fragmentFunction = library.makeFunction(name: "surface_fragment")
        descriptor.colorAttachments[0].pixelFormat = .bgra8Unorm_srgb
        descriptor.depthAttachmentPixelFormat = .depth32Float
        descriptor.rasterSampleCount = sampleCount
        pipeline = try device.makeRenderPipelineState(descriptor: descriptor)
        let depthDescriptor = MTLDepthStencilDescriptor()
        depthDescriptor.depthCompareFunction = .lessEqual; depthDescriptor.isDepthWriteEnabled = true
        guard let depth = device.makeDepthStencilState(descriptor: depthDescriptor),
              let weights = atlas.interpolationWeights.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }) else {
            throw SurfaceRenderError("Unable to allocate surface resources.")
        }
        self.depth = depth; self.weights = weights
        let ghostDescriptor = MTLDepthStencilDescriptor()
        ghostDescriptor.depthCompareFunction = .always; ghostDescriptor.isDepthWriteEnabled = false
        guard let ghost = device.makeDepthStencilState(descriptor: ghostDescriptor) else { throw SurfaceRenderError("No reference depth state.") }
        self.ghostDepth = ghost
        super.init()
    }

    @discardableResult func update(_ input: StateSurfaceRenderInput) throws -> Bool {
        guard current != input else { return false }
        guard input.values.count == 128, input.values.allSatisfy(\.isFinite), input.lower.isFinite,
              input.upper.isFinite, input.lower < input.upper, (0..<128).contains(input.selectedNode) else {
            throw SurfaceRenderError("Invalid state-surface observation.")
        }
        let shapeChanged = current.map { $0.values != input.values || $0.lower != input.lower || $0.upper != input.upper || $0.fillPct != input.fillPct || $0.relief != input.relief } ?? true
        let nextMesh = try shapeChanged ? StateSurfaceMath.mesh(values: input.values, scale: input.lower...input.upper, fillPct: input.fillPct, relief: input.relief) : mesh!
        let values = input.values.map(Float.init)
        guard let nodes = values.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }) else {
            throw SurfaceRenderError("Unable to allocate an observation buffer.")
        }
        var nextDraws: [SurfaceDraw] = []
        func append(_ vertices: [SurfaceVertex], _ primitive: MTLPrimitiveType, reference: Bool = false) throws {
            guard !vertices.isEmpty else { return }
            guard let buffer = vertices.withUnsafeBytes({ device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }) else {
                throw SurfaceRenderError("Unable to allocate surface vertices.")
            }
            nextDraws.append(SurfaceDraw(buffer: buffer, count: vertices.count, primitive: primitive, reference: reference))
        }
        var triangles: [SurfaceVertex] = []
        for face in input.cutaway ? atlas.backTriangles : atlas.triangles {
            for raw in [face.x, face.y, face.z] {
                let i = Int(raw)
                triangles.append(SurfaceVertex(nextMesh.positions[i], nextMesh.normals[i], SIMD4(Float(i), 0, 0, 0)))
            }
        }
        try append(triangles, .triangle)
        if input.cutaway && input.fillPct > 0 {
            var cap: [SurfaceVertex] = []
            for i in atlas.cutBoundary.indices {
                let a = Int(atlas.cutBoundary[i]), b = Int(atlas.cutBoundary[(i + 1) % atlas.cutBoundary.count])
                cap.append(SurfaceVertex(.zero, SIMD3(0,0,1), SIMD4(0,3,0,0)))
                cap.append(SurfaceVertex(nextMesh.positions[a], SIMD3(0,0,1), SIMD4(0,3,0,0)))
                cap.append(SurfaceVertex(nextMesh.positions[b], SIMD3(0,0,1), SIMD4(0,3,0,0)))
            }
            try append(cap, .triangle)
        }
        var lines: [SurfaceVertex] = []
        func ring(_ radius: Float, axis: Int, code: Float, dashed: Bool = false) {
            for i in 0..<192 where !dashed || i % 6 < 3 {
                for index in [i, i+1] {
                    let a = Float(index) / 192 * 2 * .pi
                    let p: SIMD3<Float> = axis == 0 ? SIMD3(0,radius*cos(a),radius*sin(a)) : axis == 1 ? SIMD3(radius*cos(a),0,radius*sin(a)) : SIMD3(radius*cos(a),radius*sin(a),0)
                    lines.append(SurfaceVertex(p, .zero, SIMD4(0,1,code,0)))
                }
            }
        }
        for axis in 0..<3 { ring(1.002, axis: axis, code: 0) }
        // This exact reference carries the scalar fill; local lobes never classify a rail.
        for axis in 0..<3 { ring(Float(nextMesh.referenceRadius), axis: axis, code: 1, dashed: true) }
        try append(lines, .line, reference: true)
        if input.showSites && input.fillPct > 0 {
            var sites: [SurfaceVertex] = []
            for i in atlas.sites.indices where !input.cutaway || atlas.sites[i].z <= 0 {
                let p = nextMesh.sitePositions[i] + atlas.sites[i] * 0.006
                sites.append(SurfaceVertex(p, atlas.sites[i], SIMD4(Float(i),2,0,i == input.selectedNode ? 1 : 0)))
            }
            try append(sites, .point)
        }
        current = input; mesh = nextMesh; nodeBuffer = nodes; draws = nextDraws
        view?.needsDisplay = true
        return true
    }
    func clear() { draws = []; mesh = nil; current = nil; nodeBuffer = nil; view?.needsDisplay = true }
    func orbit(dx: Float, dy: Float) { yaw += dx * 0.009; pitch = min(1.35,max(-1.35,pitch + dy * 0.009)); view?.needsDisplay = true }
    func zoom(delta: Float) { distance = min(7,max(2.1,distance * exp(-delta * 0.006))); view?.needsDisplay = true }
    func resetCamera() { yaw = -0.42; pitch = 0.16; distance = 3.5; view?.needsDisplay = true }
    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) { view.needsDisplay = true }
    func draw(in view: MTKView) {
        let start = ProcessInfo.processInfo.systemUptime
        guard let pass = view.currentRenderPassDescriptor, let drawable = view.currentDrawable,
              let command = queue.makeCommandBuffer() else { return }
        guard encode(command: command, pass: pass, size: view.drawableSize) else { return }
        command.present(drawable); command.commit()
        submittedFrames += 1; lastSubmitCPUms = (ProcessInfo.processInfo.systemUptime - start) * 1000
    }
    private func uniforms(size: CGSize) -> SurfaceUniforms {
        let model = simd_float4x4(simd_quatf(angle: pitch, axis: SIMD3(1,0,0))) * simd_float4x4(simd_quatf(angle: yaw, axis: SIMD3(0,1,0)))
        var camera = matrix_identity_float4x4; camera.columns.3.z = -distance
        let aspect = Float(max(1,size.width) / max(1,size.height)), y: Float = 1 / tan(0.64 / 2), near: Float = 0.1, far: Float = 30
        let projection = simd_float4x4(SIMD4(y/aspect,0,0,0), SIMD4(0,y,0,0), SIMD4(0,0,far/(near-far),-1), SIMD4(0,0,near*far/(near-far),0))
        return SurfaceUniforms(mvp: projection * camera * model, model: model,
            scale: SIMD4(Float(current?.lower ?? -1),Float(current?.upper ?? 1),current?.flatLighting == true ? 1 : 0,0))
    }
    func encode(command: MTLCommandBuffer, pass: MTLRenderPassDescriptor, size: CGSize) -> Bool {
        guard size.width > 0, size.height > 0, let encoder = command.makeRenderCommandEncoder(descriptor: pass) else { return false }
        if let nodes = nodeBuffer {
            var u = uniforms(size: size)
            encoder.setRenderPipelineState(pipeline); encoder.setDepthStencilState(depth); encoder.setCullMode(.none)
            encoder.setVertexBytes(&u, length: MemoryLayout<SurfaceUniforms>.stride, index: 1)
            encoder.setVertexBuffer(weights, offset: 0, index: 2); encoder.setVertexBuffer(nodes, offset: 0, index: 3)
            // Every generation is immutable. Metal retains buffers through completion.
            for draw in draws {
                encoder.setDepthStencilState(draw.reference ? ghostDepth : depth)
                encoder.setVertexBuffer(draw.buffer, offset: 0, index: 0)
                encoder.drawPrimitives(type: draw.primitive, vertexStart: 0, vertexCount: draw.count)
            }
        }
        encoder.endEncoding(); return true
    }
    func pick(point: CGPoint, size: CGSize) -> Int? {
        guard let mesh, let current, size.width > 0, size.height > 0 else { return nil }
        let inverse = uniforms(size: size).mvp.inverse
        let x = Float(2*point.x/size.width-1), y = Float(1-2*point.y/size.height)
        let a = inverse * SIMD4(x,y,0,1), b = inverse * SIMD4(x,y,1,1)
        let origin = SIMD3(a.x,a.y,a.z)/a.w, ray = simd_normalize(SIMD3(b.x,b.y,b.z)/b.w-origin)
        var nearest = Float.infinity
        for f in current.cutaway ? atlas.backTriangles : atlas.triangles {
            let p = mesh.positions[Int(f.x)], e1 = mesh.positions[Int(f.y)]-p, e2 = mesh.positions[Int(f.z)]-p
            let h = simd_cross(ray,e2), determinant = simd_dot(e1,h)
            if abs(determinant) < 1e-7 { continue }
            let s = origin-p, u = simd_dot(s,h)/determinant
            if u < 0 || u > 1 { continue }
            let q = simd_cross(s,e1), v = simd_dot(ray,q)/determinant
            if v < 0 || u+v > 1 { continue }
            let t = simd_dot(e2,q)/determinant
            if t > 0 { nearest = min(nearest,t) }
        }
        guard nearest.isFinite else { return nil }
        // The opaque cut face contains no state field. Do not pick through it.
        if current.cutaway && abs(ray.z) > 1e-7 {
            let t = -origin.z / ray.z
            if t > 0 && t < nearest - 1e-5 {
                let hit = origin + ray*t
                for i in atlas.cutBoundary.indices {
                    let a = mesh.positions[Int(atlas.cutBoundary[i])], b = mesh.positions[Int(atlas.cutBoundary[(i+1)%atlas.cutBoundary.count])]
                    let determinant = a.x*b.y-a.y*b.x
                    if abs(determinant) < 1e-9 { continue }
                    let u = (hit.x*b.y-hit.y*b.x)/determinant, v = (a.x*hit.y-a.y*hit.x)/determinant
                    if u >= 0 && v >= 0 && u+v <= 1 { return nil }
                }
            }
        }
        let direction = simd_normalize(origin + ray*nearest)
        return atlas.sites.indices.filter { !current.cutaway || atlas.sites[$0].z <= 0 }.max { simd_dot(atlas.sites[$0],direction) < simd_dot(atlas.sites[$1],direction) }
    }

    static let shader = """
    #include <metal_stdlib>
    using namespace metal;
    struct V { float4 p; float4 n; float4 info; };
    struct U { float4x4 mvp; float4x4 model; float4 scale; };
    struct O { float4 p [[position]]; float3 color; float pointSize [[point_size]]; float marker; };
    float field(uint index, device const float* weights, device const float* values) {
        float result=0; for(uint i=0;i<128;i++) result += weights[index*128+i]*values[i]; return result;
    }
    float3 mappedColor(float value, float2 range) {
        float t=clamp((value-range.x)/(range.y-range.x),0.0f,1.0f);
        float3 dark=float3(0.10,0.17,0.23), low=float3(0.52,0.30,0.92), high=float3(0.14,0.91,0.79);
        if(range.x>=0) return mix(dark,high,t);
        return t<0.5 ? mix(low,dark,t*2) : mix(dark,high,(t-0.5)*2);
    }
    vertex O surface_vertex(uint id [[vertex_id]], device const V* vertices [[buffer(0)]],
        constant U& u [[buffer(1)]], device const float* weights [[buffer(2)]], device const float* values [[buffer(3)]]) {
        V v=vertices[id]; O o; o.p=u.mvp*v.p; o.pointSize=3.5; o.marker=0;
        uint kind=uint(v.info.y); float value=0;
        if(kind==0) value=field(uint(v.info.x),weights,values);
        if(kind==2) { value=values[uint(v.info.x)]; o.pointSize=v.info.w>0 ? 12 : 4; o.marker=1; }
        o.color=mappedColor(value,u.scale.xy);
        if(kind==0 && u.scale.z<0.5) {
            float3 n=normalize((u.model*v.n).xyz);
            float light=0.48+0.52*max(0.0f,dot(n,normalize(float3(-0.5,0.8,1))));
            o.color*=light; o.color+=float3(0.10,0.17,0.20)*pow(max(0.0f,n.z),18.0f);
        }
        if(kind==1) o.color=v.info.z>0 ? float3(0.67,0.84,0.90) : float3(0.15,0.24,0.32);
        if(kind==2 && v.info.w>0) o.color=float3(1,0.85,0.52);
        if(kind==3) o.color=float3(0.035,0.07,0.10); // unmeasured cut face, not interpolated state
        return o;
    }
    fragment float4 surface_fragment(O in [[stage_in]], float2 point [[point_coord]]) {
        if(in.marker>0.5 && length(point-0.5)>0.5) discard_fragment();
        return float4(in.color,1);
    }
    kernel void surface_field_check(device const float* weights [[buffer(0)]], device const float* values [[buffer(1)]],
        device float* output [[buffer(2)]], constant uint& count [[buffer(3)]], uint index [[thread_position_in_grid]]) {
        if(index<count) output[index]=field(index,weights,values);
    }
    """
}
