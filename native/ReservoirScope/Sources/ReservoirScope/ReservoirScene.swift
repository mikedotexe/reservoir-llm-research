import SwiftUI
import MetalKit
import simd

enum ReservoirSceneMode: String, CaseIterable, Identifiable {
    case fill, zones, surface, response, trajectory, spectral
    var id: String { rawValue }
}

/// Shared geometry for the Metal lens and native labels. The crop is framing,
/// not a pair of regulator thresholds. Screen coordinates have a top-left origin.
enum ReferenceLens {
    static let lowerFillPct = 54.0
    static let upperFillPct = 82.0
    static let magnification = 12.0
    static let halfAngle = 0.128
    static let returnAngle = 0.14

    static func radius(fillPct: Double) -> Double {
        pow(min(1, max(0, fillPct / 100)), 1.0 / 3.0)
    }

    static func modelPoint(radius: Double, angle: Double, longitude: Double = 0) -> SIMD3<Double> {
        let center = (self.radius(fillPct: lowerFillPct) + self.radius(fillPct: upperFillPct)) / 2
        let original = SIMD3(radius * cos(angle) * cos(longitude), radius * sin(angle),
            -radius * cos(angle) * sin(longitude))
        return (original - SIMD3(center, 0, 0)) * magnification
    }

    static func orthographicHalfHeight(aspect: Double) -> Double {
        let safeAspect = aspect.isFinite && aspect > 0 ? aspect : 1
        return max(1.52, 0.96 / safeAspect)
    }

    /// Positions a label on the exact front cut-face arc. Uniform projection
    /// matches Metal at any viewport size; callers choose leader/label offsets.
    static func point(fillPct: Double, angle: Double, width: Double, height: Double) -> (x: Double, y: Double) {
        guard fillPct.isFinite, angle.isFinite, width.isFinite, height.isFinite,
              width > 0, height > 0 else { return (.nan, .nan) }
        let aspect = width / height
        let halfHeight = orthographicHalfHeight(aspect: aspect)
        let halfWidth = halfHeight * aspect
        let p = modelPoint(radius: radius(fillPct: fillPct), angle: angle)
        return ((0.5 + p.x / (2 * halfWidth)) * width,
            (0.5 - p.y / (2 * halfHeight)) * height)
    }
}

/// Native Metal view. All geometry comes from explicit scalar mappings or the
/// supplied recorded PCA coordinates; no synthetic state samples are generated.
struct ReservoirScene: NSViewRepresentable {
    var mode: ReservoirSceneMode
    var fillPct: Double
    var points: [[Double]]
    var selectedIndex: Int
    var referenceRadius: Double
    var cutaway: Bool
    var showBands: Bool
    var spectralValues: [Double] = []
    var componentVariances: [Double] = []
    var zoneThresholds: [Double] = []
    var selectedZonePct: Double? = nil
    var zoneShelfBounds: [Double] = []
    var smoothFill = false
    var fillSourceIsFresh = false
    var fillSourceContext = "recorded"
    var fillSourceTime: Double? = nil

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> ReservoirMetalView {
        let view = ReservoirMetalView(frame: .zero, device: MTLCreateSystemDefaultDevice())
        view.colorPixelFormat = .bgra8Unorm_srgb
        view.depthStencilPixelFormat = .depth32Float
        view.sampleCount = view.device?.supportsTextureSampleCount(4) == true ? 4 : 1
        view.clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        view.isPaused = true
        view.preferredFramesPerSecond = 60
        view.enableSetNeedsDisplay = true
        view.framebufferOnly = true
        view.wantsLayer = true
        do {
            let renderer = try ReservoirMetalRenderer(view: view)
            context.coordinator.renderer = renderer
            view.sceneRenderer = renderer
            view.delegate = renderer
        } catch {
            let message = NSTextField(wrappingLabelWithString: "Metal renderer unavailable: \(error.localizedDescription)")
            message.textColor = .secondaryLabelColor
            message.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(message)
            NSLayoutConstraint.activate([
                message.centerYAnchor.constraint(equalTo: view.centerYAnchor),
                message.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24),
                message.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24)
            ])
        }
        return view
    }

    func updateNSView(_ view: ReservoirMetalView, context: Context) {
        let state = ReservoirSceneState(mode: mode, fillPct: fillPct, points: points,
            selectedIndex: selectedIndex, referenceRadius: referenceRadius,
            cutaway: cutaway, showBands: showBands, spectralValues: spectralValues,
            zoneThresholds: zoneThresholds, selectedZonePct: selectedZonePct,
            zoneShelfBounds: zoneShelfBounds)
        context.coordinator.renderer?.update(state, smoothFill: smoothFill,
            animated: fillSourceIsFresh, context: fillSourceContext, sourceTime: fillSourceTime)
        let presentation = smoothFill
            ? " The cyan surface eases toward the latest observation over 0.8 seconds. The white dashed marker shows the measured fill immediately."
            : " The surface shows the measured fill directly."
        view.setAccessibilityLabel(mode == .fill
            ? "Reservoir fill sphere, measured fill \(String(format: "%.1f", fillPct)) percent." + presentation
            : mode == .zones
                ? "Reference zones. Fixed orthographic detail of the sphere's cut face, magnified twelve times. Measured fill is \(String(format: "%.1f", fillPct)) percent." + presentation + " Select a reference in the inspector to highlight its boundary."
            : mode == .trajectory
                ? "Recorded state trajectory in three frozen principal components. Drag to orbit, scroll to zoom."
                : "Three recorded spectral magnitudes, square-root scale on schematic axes.")
    }

    final class Coordinator {
        fileprivate var renderer: ReservoirMetalRenderer?
    }

    static func dismantleNSView(_ view: ReservoirMetalView, coordinator: Coordinator) {
        view.isPaused = true
        view.delegate = nil
        coordinator.renderer = nil
    }
}

final class ReservoirMetalView: MTKView {
    fileprivate weak var sceneRenderer: ReservoirMetalRenderer?
    override var acceptsFirstResponder: Bool { true }
    override func mouseDown(with event: NSEvent) { window?.makeFirstResponder(self) }
    override func mouseDragged(with event: NSEvent) {
        sceneRenderer?.orbit(dx: Float(event.deltaX), dy: Float(event.deltaY))
    }
    override func scrollWheel(with event: NSEvent) {
        sceneRenderer?.zoom(delta: Float(event.scrollingDeltaY))
    }
    override func magnify(with event: NSEvent) {
        sceneRenderer?.zoom(delta: Float(event.magnification) * 180)
    }
    override func mouseUp(with event: NSEvent) {
        if event.clickCount == 2 { sceneRenderer?.resetCamera() }
    }
    override func keyDown(with event: NSEvent) {
        switch event.keyCode {
        case 123: sceneRenderer?.orbit(dx: -12, dy: 0)
        case 124: sceneRenderer?.orbit(dx: 12, dy: 0)
        case 125: sceneRenderer?.orbit(dx: 0, dy: 12)
        case 126: sceneRenderer?.orbit(dx: 0, dy: -12)
        case 49: sceneRenderer?.resetCamera()
        default: super.keyDown(with: event)
        }
    }
}

struct ReservoirSceneState: Equatable {
    var mode: ReservoirSceneMode
    var fillPct: Double
    var points: [[Double]]
    var selectedIndex: Int
    var referenceRadius: Double
    var cutaway: Bool
    var showBands: Bool
    var spectralValues: [Double]
    var zoneThresholds: [Double]
    var selectedZonePct: Double?
    var zoneShelfBounds: [Double]
}

/// Only these inputs affect fixed fill/reference meshes. Camera changes use
/// uniforms; incoming samples and presentation frames reuse these buffers.
private struct FillReferenceStyle: Equatable {
    let mode: ReservoirSceneMode
    let cutaway: Bool
    let showBands: Bool
    let thresholds: [Double]
    let selected: Double?
    let shelf: [Double]
    init(_ state: ReservoirSceneState) {
        mode = state.mode; cutaway = state.cutaway; showBands = state.showBands
        thresholds = state.zoneThresholds; selected = state.selectedZonePct; shelf = state.zoneShelfBounds
    }
}

private struct SceneVertex {
    var position: SIMD4<Float>
    var normal: SIMD4<Float>
    var color: SIMD4<Float>
    init(_ position: SIMD3<Float>, normal: SIMD3<Float> = .zero, color: SIMD4<Float>) {
        self.position = SIMD4(position, 1)
        self.normal = SIMD4(normal, 0)
        self.color = color
    }
}

private struct SceneUniforms {
    var mvp: simd_float4x4
    var model: simd_float4x4
}

private struct SceneDraw {
    let buffer: MTLBuffer
    let count: Int
    let primitive: MTLPrimitiveType
}

private enum SceneFailure: LocalizedError {
    case metalUnavailable, pipelineUnavailable
    var errorDescription: String? {
        switch self {
        case .metalUnavailable: return "This Mac did not provide a Metal device."
        case .pipelineUnavailable: return "The GPU pipeline could not be created."
        }
    }
}

final class ReservoirMetalRenderer: NSObject, MTKViewDelegate {
    private weak var view: MTKView?
    private let device: MTLDevice
    private let queue: MTLCommandQueue
    private let pipeline: MTLRenderPipelineState
    private let depthState: MTLDepthStencilState
    private var state: ReservoirSceneState?
    private var draws: [SceneDraw] = []
    private var fixedDraws: [String: [SceneDraw]] = [:]
    private var referenceStyle: FillReferenceStyle?
    private var fillTransition = FillTransition()
    private var renderedFill: Double?
    private var showMeasuredFill = false
    private var yaw: Float = -0.42
    private var pitch: Float = 0.16
    private var distance: Float = 3.8

    private let cyan = SIMD4<Float>(0.10, 0.70, 0.83, 1)
    private let green = SIMD4<Float>(0.29, 0.82, 0.63, 1)
    private let amber = SIMD4<Float>(1.0, 0.64, 0.26, 1)
    private let violet = SIMD4<Float>(0.67, 0.56, 0.95, 1)
    private let white = SIMD4<Float>(0.66, 0.77, 0.85, 1)

    convenience init(view: MTKView) throws {
        guard let device = view.device else { throw SceneFailure.metalUnavailable }
        try self.init(device: device, sampleCount: view.sampleCount,
            colorPixelFormat: view.colorPixelFormat, depthPixelFormat: view.depthStencilPixelFormat)
        self.view = view
    }

    init(device: MTLDevice, sampleCount: Int, colorPixelFormat: MTLPixelFormat = .bgra8Unorm_srgb,
         depthPixelFormat: MTLPixelFormat = .depth32Float) throws {
        guard let queue = device.makeCommandQueue() else { throw SceneFailure.metalUnavailable }
        self.device = device
        self.queue = queue
        let library = try device.makeLibrary(source: Self.shader, options: nil)
        let descriptor = MTLRenderPipelineDescriptor()
        descriptor.label = "ReservoirScope immutable geometry"
        descriptor.vertexFunction = library.makeFunction(name: "reservoirVertex")
        descriptor.fragmentFunction = library.makeFunction(name: "reservoirFragment")
        descriptor.colorAttachments[0].pixelFormat = colorPixelFormat
        descriptor.depthAttachmentPixelFormat = depthPixelFormat
        descriptor.rasterSampleCount = sampleCount
        descriptor.colorAttachments[0].isBlendingEnabled = true
        descriptor.colorAttachments[0].rgbBlendOperation = .add
        descriptor.colorAttachments[0].alphaBlendOperation = .add
        descriptor.colorAttachments[0].sourceRGBBlendFactor = .sourceAlpha
        descriptor.colorAttachments[0].destinationRGBBlendFactor = .oneMinusSourceAlpha
        descriptor.colorAttachments[0].sourceAlphaBlendFactor = .one
        descriptor.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha
        self.pipeline = try device.makeRenderPipelineState(descriptor: descriptor)
        let depth = MTLDepthStencilDescriptor()
        depth.depthCompareFunction = .lessEqual
        // Instrument shells are transparent context. Avoid obscuring trajectory
        // segments behind the shell; geometry is deliberately drawn back to front.
        depth.isDepthWriteEnabled = false
        guard let depthState = device.makeDepthStencilState(descriptor: depth) else {
            throw SceneFailure.pipelineUnavailable
        }
        self.depthState = depthState
        super.init()
    }

    func update(_ newState: ReservoirSceneState, smoothFill: Bool = false,
                animated: Bool = false, context: String = "recorded", sourceTime: Double? = nil) {
        let now = ProcessInfo.processInfo.systemUptime
        let fillMode = newState.mode == .fill || newState.mode == .zones
        let markerChanged = showMeasuredFill != (smoothFill && fillMode)
        showMeasuredFill = smoothFill && fillMode
        fillTransition.receive(newState.fillPct, at: now,
            animated: smoothFill && animated && fillMode, context: context, sourceTime: sourceTime)
        let changed = state != newState
        state = newState
        let displayFill = fillMode ? (fillTransition.value(at: now) ?? newState.fillPct) : newState.fillPct
        configureDrawLoop(at: now)
        if changed || markerChanged || renderedFill != displayFill {
            rebuildPresentation(fillPct: displayFill)
            view?.needsDisplay = true
        }
    }

    private func configureDrawLoop(at uptime: TimeInterval) {
        guard let view else { return }
        let active = (state?.mode == .fill || state?.mode == .zones) && fillTransition.isAnimating(at: uptime)
        if active {
            if view.enableSetNeedsDisplay { view.enableSetNeedsDisplay = false }
            if view.isPaused { view.isPaused = false }
        } else {
            if !view.isPaused { view.isPaused = true }
            if !view.enableSetNeedsDisplay { view.enableSetNeedsDisplay = true }
        }
    }

    private func rebuildPresentation(fillPct: Double) {
        guard var presentation = state else { return }
        presentation.fillPct = fillPct
        renderedFill = fillPct
        rebuild(presentation)
    }

    func orbit(dx: Float, dy: Float) {
        guard state?.mode != .zones else { return }
        yaw += dx * 0.009
        pitch = min(1.35, max(-1.35, pitch + dy * 0.009))
        view?.needsDisplay = true
    }

    func zoom(delta: Float) {
        guard state?.mode != .zones else { return }
        distance = min(7.0, max(2.2, distance * exp(-delta * 0.006)))
        view?.needsDisplay = true
    }

    func resetCamera() {
        yaw = -0.42; pitch = 0.16; distance = 3.8
        view?.needsDisplay = true
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        view.needsDisplay = true
    }

    func draw(in view: MTKView) {
        let now = ProcessInfo.processInfo.systemUptime
        if state?.mode == .fill || state?.mode == .zones {
            if let fill = fillTransition.value(at: now), fill != renderedFill {
                rebuildPresentation(fillPct: fill)
            }
            // Display-linked redraws exist only during a bounded transition.
            // No incoming reading means no further motion or extrapolation.
            configureDrawLoop(at: now)
        }
        guard view.drawableSize.width > 0, view.drawableSize.height > 0,
              let pass = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let command = queue.makeCommandBuffer() else { return }
        guard encodeScene(commandBuffer: command, renderPass: pass, drawableSize: view.drawableSize) else { return }
        command.present(drawable)
        command.commit()
    }

    var drawCount: Int { draws.count }
    var vertexCount: Int { draws.reduce(0) { $0 + $1.count } }
    var bufferBytes: Int { draws.reduce(0) { $0 + $1.buffer.length } }

    /// Same pipeline and commands for an on-screen drawable or a bounded
    /// offscreen benchmark. The caller owns presentation, commit and completion.
    func encodeScene(commandBuffer: MTLCommandBuffer, renderPass: MTLRenderPassDescriptor,
                     drawableSize: CGSize) -> Bool {
        guard drawableSize.width > 0, drawableSize.height > 0,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: renderPass) else { return false }
        let aspect = Float(drawableSize.width / drawableSize.height)
        let isZones = state?.mode == .zones
        let model = isZones ? matrix_identity_float4x4
            : simd_float4x4(simd_quatf(angle: pitch, axis: SIMD3(1, 0, 0)))
                * simd_float4x4(simd_quatf(angle: yaw, axis: SIMD3(0, 1, 0)))
        var camera = matrix_identity_float4x4
        camera.columns.3 = SIMD4(0, 0, isZones ? -3.8 : -distance, 1)
        let projection = isZones ? Self.orthographic(aspect: aspect) : Self.perspective(aspect: aspect)
        var uniforms = SceneUniforms(mvp: projection * camera * model, model: model)
        encoder.setRenderPipelineState(pipeline)
        encoder.setDepthStencilState(depthState)
        encoder.setCullMode(.none)
        encoder.setVertexBytes(&uniforms, length: MemoryLayout<SceneUniforms>.stride, index: 1)
        // Each draw owns an immutable shared buffer. Metal retains submitted
        // resources until completion, so selection updates cannot overwrite data
        // still in use by the GPU. Uniform bytes are copied by the command encoder.
        let submittedDraws = draws
        for draw in submittedDraws {
            encoder.setVertexBuffer(draw.buffer, offset: 0, index: 0)
            encoder.drawPrimitives(type: draw.primitive, vertexStart: 0, vertexCount: draw.count)
        }
        encoder.endEncoding()
        return true
    }

    private func rebuild(_ state: ReservoirSceneState) {
        let style = FillReferenceStyle(state)
        if referenceStyle != style {
            fixedDraws.removeAll(keepingCapacity: true)
            referenceStyle = style
        }
        draws = []
        switch state.mode {
        case .fill: makeFill(state)
        case .zones: makeZones(state)
        case .trajectory: makeTrajectory(state)
        case .spectral: makeSpectral(state)
        case .surface, .response: break // These views have their own field/relief renderer.
        }
    }

    private func fixedGeometry(_ key: String, make: () -> Void) {
        if let cached = fixedDraws[key] { draws.append(contentsOf: cached); return }
        let start = draws.count
        make()
        fixedDraws[key] = Array(draws[start...])
    }

    private func append(_ vertices: [SceneVertex], primitive: MTLPrimitiveType) {
        guard !vertices.isEmpty else { return }
        let buffer = vertices.withUnsafeBytes { bytes in
            device.makeBuffer(bytes: bytes.baseAddress!, length: bytes.count, options: .storageModeShared)
        }
        if let buffer { draws.append(SceneDraw(buffer: buffer, count: vertices.count, primitive: primitive)) }
    }

    private func tint(_ value: SIMD4<Float>, _ alpha: Float) -> SIMD4<Float> {
        SIMD4(value.x, value.y, value.z, alpha)
    }

    private func fillRadius(_ percent: Double) -> Float {
        Float(pow(min(1, max(0, percent / 100)), 1.0 / 3.0))
    }

    private func makeFill(_ state: ReservoirSceneState) {
        fixedGeometry("fill-context") {
            cage(alpha: 0.15, cutaway: state.cutaway)
            if state.showBands {
                if state.cutaway {
                    annulus(inner: fillRadius(58), outer: fillRadius(72), color: tint(green, 0.14))
                }
                circle(radius: fillRadius(58), color: tint(green, 0.48))
                circle(radius: fillRadius(72), color: tint(green, 0.75))
                circle(radius: fillRadius(68), color: tint(white, 0.75), dashed: true)
                circle(radius: fillRadius(74), color: tint(amber, 0.55), dashed: true)
                circle(radius: fillRadius(78), color: SIMD4(1, 0.34, 0.32, 0.65), dashed: true)
            }
        }
        let radius = fillRadius(state.fillPct.isFinite ? state.fillPct : 0)
        sphere(radius: radius, color: tint(cyan, state.cutaway ? 0.36 : 0.24), cutaway: state.cutaway)
        if state.cutaway { annulus(inner: 0, outer: radius, color: tint(cyan, 0.10)) }
        circle(radius: radius, color: tint(cyan, 0.95))
        if showMeasuredFill, let measured = self.state?.fillPct, measured.isFinite {
            circle(radius: fillRadius(measured), color: tint(white, 0.9), dashed: true)
        }
        fixedGeometry("fill-foreground") {
            circle(radius: 1, color: tint(white, 0.56))
            append([
                SceneVertex(SIMD3(0, 0, 0.008), color: tint(white, 0.52)),
                SceneVertex(SIMD3(1, 0, 0.008), color: tint(white, 0.52))
            ], primitive: .line)
            sphere(radius: 0.011, color: tint(white, 1))
        }
    }

    /// A magnifying lens on a real spherical cross-section. These two fill
    /// values define only the crop, never regulator limits. Every point uses
    /// the same translation and uniform scale; thin gaps are not widened.
    private func makeZones(_ state: ReservoirSceneState) {
        let cropLow = fillRadius(ReferenceLens.lowerFillPct), cropHigh = fillRadius(ReferenceLens.upperFillPct)
        let halfAngle = Float(ReferenceLens.halfAngle)
        let returnAngle = Float(ReferenceLens.returnAngle)
        let steps = 144

        func point(radius: Float, angle: Float, longitude: Float = 0) -> SIMD3<Float> {
            let p = ReferenceLens.modelPoint(radius: Double(radius), angle: Double(angle), longitude: Double(longitude))
            return SIMD3(Float(p.x), Float(p.y), Float(p.z))
        }

        func arc(radius: Float, color: SIMD4<Float>, dashed: Bool = false,
                 longitude: Float = 0) {
            var vertices: [SceneVertex] = []
            for index in 0..<steps {
                if dashed && index % 12 >= 7 { continue }
                let a = -halfAngle + Float(index) / Float(steps) * 2 * halfAngle
                let b = -halfAngle + Float(index + 1) / Float(steps) * 2 * halfAngle
                vertices.append(SceneVertex(point(radius: radius, angle: a, longitude: longitude), color: color))
                vertices.append(SceneVertex(point(radius: radius, angle: b, longitude: longitude), color: color))
            }
            append(vertices, primitive: .line)
        }

        func face(inner: Float, outer: Float, color: SIMD4<Float>) {
            guard outer > inner else { return }
            var vertices: [SceneVertex] = []
            for index in 0..<steps {
                let a = -halfAngle + Float(index) / Float(steps) * 2 * halfAngle
                let b = -halfAngle + Float(index + 1) / Float(steps) * 2 * halfAngle
                let p = point(radius: inner, angle: a), q = point(radius: outer, angle: a)
                let r = point(radius: outer, angle: b), s = point(radius: inner, angle: b)
                for position in [p, q, r, p, r, s] {
                    vertices.append(SceneVertex(position, color: color))
                }
            }
            append(vertices, primitive: .triangle)
        }

        func sphericalReturn(radius: Float, color: SIMD4<Float>) {
            var vertices: [SceneVertex] = []
            let columns = 10
            for row in 0..<steps {
                let a = -halfAngle + Float(row) / Float(steps) * 2 * halfAngle
                let b = -halfAngle + Float(row + 1) / Float(steps) * 2 * halfAngle
                for column in 0..<columns {
                    let u = Float(column) / Float(columns) * returnAngle
                    let v = Float(column + 1) / Float(columns) * returnAngle
                    for (angle, longitude) in [(a, u), (b, u), (b, v), (a, u), (b, v), (a, v)] {
                        let normal = SIMD3(cos(angle) * cos(longitude), sin(angle),
                            -cos(angle) * sin(longitude))
                        vertices.append(SceneVertex(point(radius: radius, angle: angle, longitude: longitude),
                            normal: normal, color: color))
                    }
                }
            }
            append(vertices, primitive: .triangle)
        }

        // The faint rear edge and spherical return orient the slice in space.
        // Neither edge is an extra reference boundary.
        let shelf = state.zoneShelfBounds.filter { $0.isFinite && (0...100).contains($0) }.sorted()
        fixedGeometry("zones-context") {
            sphericalReturn(radius: cropHigh, color: tint(white, 0.045))
            arc(radius: cropHigh, color: tint(white, 0.11), longitude: returnAngle)
            face(inner: cropLow, outer: cropHigh, color: tint(white, 0.035))

            if shelf.count == 2 {
                face(inner: max(cropLow, fillRadius(shelf[0])),
                    outer: min(cropHigh, fillRadius(shelf[1])), color: tint(green, 0.17))
            }
        }

        if state.fillPct.isFinite {
            let fill = fillRadius(state.fillPct)
            face(inner: cropLow, outer: min(cropHigh, fill), color: tint(cyan, 0.17))
            if (cropLow...cropHigh).contains(fill) {
                sphericalReturn(radius: fill, color: tint(cyan, 0.28))
                arc(radius: fill, color: tint(cyan, 0.26), longitude: returnAngle)
            }
        }

        // The radial guide is a measuring direction, with tick marks on each
        // supplied reference. Threshold meanings live in the shared UI model.
        fixedGeometry("zones-references") {
            append([
                SceneVertex(point(radius: cropLow, angle: 0), color: tint(white, 0.22)),
                SceneVertex(point(radius: cropHigh, angle: 0), color: tint(white, 0.22))
            ], primitive: .line)
            let thresholds = Set(state.zoneThresholds.filter {
                $0.isFinite && (ReferenceLens.lowerFillPct...ReferenceLens.upperFillPct).contains($0)
            }).sorted()
            for percent in thresholds {
                let radius = fillRadius(percent)
                let selected = state.selectedZonePct.map { abs($0 - percent) < 0.00001 } ?? false
                let isShelfEdge = shelf.contains { abs($0 - percent) < 0.00001 }
                let color = selected ? violet : (isShelfEdge ? green : white)
                if selected {
                    // A constant screen treatment around the exact boundary, not
                    // a changed limit or an implied uncertainty interval.
                    face(inner: radius - 0.00035, outer: radius + 0.00035, color: tint(violet, 0.88))
                }
                arc(radius: radius, color: tint(color, selected ? 1 : 0.65), dashed: !selected && !isShelfEdge)
                let tick = point(radius: radius, angle: 0)
                append([
                    SceneVertex(tick + SIMD3(0, -0.036, 0), color: color),
                    SceneVertex(tick + SIMD3(0, 0.036, 0), color: color)
                ], primitive: .line)
            }
        }

        if state.fillPct.isFinite {
            let radius = fillRadius(state.fillPct)
            if (cropLow...cropHigh).contains(radius) {
                arc(radius: radius, color: tint(cyan, 1))
                sphere(radius: 0.019, center: point(radius: radius, angle: 0), color: cyan)
            }
        }
        if showMeasuredFill, let measured = self.state?.fillPct, measured.isFinite {
            let radius = fillRadius(measured)
            if (cropLow...cropHigh).contains(radius) {
                arc(radius: radius, color: tint(white, 0.95), dashed: true)
                sphere(radius: 0.014, center: point(radius: radius, angle: 0), color: tint(white, 1))
            }
        }
    }

    private func makeTrajectory(_ state: ReservoirSceneState) {
        cage(alpha: 0.105, cutaway: state.cutaway)
        axes(alpha: 0.30)
        let denominator = Float(state.referenceRadius.isFinite && state.referenceRadius > 0
            ? state.referenceRadius : 1)
        var segment: [SceneVertex] = []
        let count = state.points.count
        for (index, point) in state.points.enumerated() {
            guard point.count >= 3, point.prefix(3).allSatisfy(\.isFinite) else {
                append(segment, primitive: .lineStrip); segment = []; continue
            }
            let position = SIMD3(Float(point[0]), Float(point[1]), Float(point[2])) / denominator
            let progress = Float(index) / Float(max(1, count - 1))
            let color = SIMD4<Float>(0.10 + 0.12 * progress, 0.34 + 0.48 * progress,
                0.53 + 0.35 * progress, 0.25 + 0.68 * progress)
            segment.append(SceneVertex(position, color: color))
        }
        append(segment, primitive: .lineStrip)
        guard !state.points.isEmpty else { return }
        let index = min(max(0, state.selectedIndex), state.points.count - 1)
        let point = state.points[index]
        if point.count >= 3 && point.prefix(3).allSatisfy(\.isFinite) {
            let position = SIMD3(Float(point[0]), Float(point[1]), Float(point[2])) / denominator
            append([SceneVertex(.zero, color: tint(amber, 0.18)),
                SceneVertex(position, color: tint(amber, 0.4))], primitive: .line)
            sphere(radius: 0.020, center: position, color: amber)
            sphere(radius: 0.031, center: position, color: tint(amber, 0.16))
        }
    }

    private func makeSpectral(_ state: ReservoirSceneState) {
        cage(alpha: 0.12, cutaway: state.cutaway)
        let denominator = Float(state.referenceRadius.isFinite && state.referenceRadius > 0
            ? state.referenceRadius : 1)
        let directions: [SIMD3<Float>] = [SIMD3(1, 0, 0), SIMD3(0, 1, 0), SIMD3(0, 0, 1)]
        let colors = [cyan, amber, violet]
        for index in 0..<min(3, state.spectralValues.count) {
            let value = state.spectralValues[index]
            guard value.isFinite, value >= 0 else { continue }
            let radius = Float(sqrt(value)) / denominator
            let endpoint = directions[index] * radius
            append([SceneVertex(-endpoint, color: tint(colors[index], 0.45)),
                    SceneVertex(endpoint, color: colors[index])], primitive: .line)
            sphere(radius: 0.022, center: endpoint, color: colors[index])
            sphere(radius: 0.014, center: -endpoint, color: tint(colors[index], 0.48))
        }
        sphere(radius: 0.011, color: tint(white, 0.8))
    }

    private func axes(alpha: Float) {
        let directions: [SIMD3<Float>] = [SIMD3(1, 0, 0), SIMD3(0, 1, 0), SIMD3(0, 0, 1)]
        for (direction, color) in zip(directions, [cyan, amber, violet]) {
            append([SceneVertex(-direction, color: tint(color, alpha * 0.5)),
                    SceneVertex(direction, color: tint(color, alpha))], primitive: .line)
        }
    }

    private func cage(alpha: Float, cutaway: Bool) {
        let color = tint(white, alpha)
        for index in 0..<6 {
            let angle = Float(index) * .pi / 6
            var vertices: [SceneVertex] = []
            for step in 0...120 {
                let t = Float(step) / 120 * 2 * .pi
                let p = SIMD3(cos(t) * cos(angle), sin(t), cos(t) * sin(angle))
                if !cutaway || p.z <= 0.0001 {
                    vertices.append(SceneVertex(p, color: color))
                } else if !vertices.isEmpty {
                    append(vertices, primitive: .lineStrip); vertices = []
                }
            }
            append(vertices, primitive: .lineStrip)
        }
        for latitude in [-0.65 as Float, -0.32, 0.32, 0.65] {
            let radius = sqrt(1 - latitude * latitude)
            var vertices: [SceneVertex] = []
            let start: Float = cutaway ? .pi : 0
            let span: Float = cutaway ? .pi : 2 * .pi
            for step in 0...120 {
                let angle = start + Float(step) / 120 * span
                vertices.append(SceneVertex(SIMD3(radius * cos(angle), latitude, radius * sin(angle)), color: color))
            }
            append(vertices, primitive: .lineStrip)
        }
        circle(radius: 1, color: tint(white, alpha * 1.8))
    }

    private func circle(radius: Float, color: SIMD4<Float>, dashed: Bool = false) {
        var vertices: [SceneVertex] = []
        for index in 0..<180 {
            if dashed && index % 8 >= 4 { continue }
            let a = Float(index) / 180 * 2 * .pi
            let b = Float(index + 1) / 180 * 2 * .pi
            vertices.append(SceneVertex(SIMD3(radius * cos(a), radius * sin(a), 0.005), color: color))
            vertices.append(SceneVertex(SIMD3(radius * cos(b), radius * sin(b), 0.005), color: color))
        }
        append(vertices, primitive: .line)
    }

    private func annulus(inner: Float, outer: Float, color: SIMD4<Float>) {
        var vertices: [SceneVertex] = []
        for index in 0..<128 {
            let a = Float(index) / 128 * 2 * .pi
            let b = Float(index + 1) / 128 * 2 * .pi
            let p = SIMD3(inner * cos(a), inner * sin(a), 0)
            let q = SIMD3(outer * cos(a), outer * sin(a), 0)
            let r = SIMD3(outer * cos(b), outer * sin(b), 0)
            let s = SIMD3(inner * cos(b), inner * sin(b), 0)
            for position in [p, q, r, p, r, s] {
                vertices.append(SceneVertex(position, color: color))
            }
        }
        append(vertices, primitive: .triangle)
    }

    private func sphere(radius: Float, center: SIMD3<Float> = .zero,
                        color: SIMD4<Float>, cutaway: Bool = false) {
        guard radius > 0 else { return }
        let rows = radius < 0.05 ? 10 : 40
        let columns = radius < 0.05 ? 16 : 64
        let start: Float = cutaway ? .pi : 0
        let span: Float = cutaway ? .pi : 2 * .pi
        func normal(_ row: Int, _ column: Int) -> SIMD3<Float> {
            let latitude = Float(row) / Float(rows) * .pi
            let longitude = start + Float(column) / Float(columns) * span
            return SIMD3(sin(latitude) * cos(longitude), cos(latitude), sin(latitude) * sin(longitude))
        }
        var vertices: [SceneVertex] = []
        vertices.reserveCapacity(rows * columns * 6)
        for row in 0..<rows {
            for column in 0..<columns {
                let a = normal(row, column), b = normal(row + 1, column)
                let c = normal(row + 1, column + 1), d = normal(row, column + 1)
                for n in [a, b, c, a, c, d] {
                    vertices.append(SceneVertex(center + n * radius, normal: n, color: color))
                }
            }
        }
        append(vertices, primitive: .triangle)
    }

    private static func perspective(aspect: Float) -> simd_float4x4 {
        let near: Float = 0.1, far: Float = 50
        let y = 1 / tan(Float.pi / 7.5)
        let z = far / (near - far)
        return simd_float4x4(columns: (
            SIMD4(y / max(aspect, 0.1), 0, 0, 0),
            SIMD4(0, y, 0, 0),
            SIMD4(0, 0, z, -1),
            SIMD4(0, 0, near * z, 0)
        ))
    }

    private static func orthographic(aspect: Float) -> simd_float4x4 {
        // Fit the whole 12× geometric detail even in a tall, narrow window.
        // Projection remains uniform in screen x/y; 12× is the model-space
        // magnification, not a fixed physical pixel-size promise.
        let safeAspect = aspect.isFinite && aspect > 0 ? aspect : 1
        let halfHeight = Float(ReferenceLens.orthographicHalfHeight(aspect: Double(safeAspect)))
        let halfWidth = halfHeight * safeAspect
        let near: Float = 0.1, far: Float = 50
        return simd_float4x4(columns: (
            SIMD4(1 / halfWidth, 0, 0, 0),
            SIMD4(0, 1 / halfHeight, 0, 0),
            SIMD4(0, 0, 1 / (near - far), 0),
            SIMD4(0, 0, near / (near - far), 1)
        ))
    }

    private static let shader = """
    #include <metal_stdlib>
    using namespace metal;
    struct Vertex { float4 position; float4 normal; float4 color; };
    struct Uniforms { float4x4 mvp; float4x4 model; };
    struct VertexOut { float4 position [[position]]; float4 color; };
    vertex VertexOut reservoirVertex(uint index [[vertex_id]],
        const device Vertex *vertices [[buffer(0)]],
        constant Uniforms &uniforms [[buffer(1)]]) {
        Vertex v = vertices[index];
        VertexOut out;
        out.position = uniforms.mvp * v.position;
        float luminance = 1.0;
        if (length(v.normal.xyz) > 0.5) {
            float3 normal = normalize((uniforms.model * v.normal).xyz);
            float light = abs(dot(normal, normalize(float3(-0.35, 0.7, 0.9))));
            luminance = 0.46 + 0.54 * light;
        }
        out.color = float4(v.color.rgb * luminance, v.color.a);
        return out;
    }
    fragment float4 reservoirFragment(VertexOut in [[stage_in]]) { return in.color; }
    """
}
