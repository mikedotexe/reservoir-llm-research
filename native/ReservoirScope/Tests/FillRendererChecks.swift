// Concatenated after FillTransition.swift and ReservoirScene.swift by the runner.
// Tiny synthetic offscreen scenes only; no window, evidence files, or live feeds.
import Foundation
import MetalKit

private struct RendererCheckFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

@MainActor private struct FillRendererChecks {
    private var passed = 0
    private let size = 256

    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw RendererCheckFailure(message: description) }
        passed += 1
        print("PASS \(passed): \(description)")
    }

    private func render(_ renderer: ReservoirMetalRenderer, device: MTLDevice,
                        queue: MTLCommandQueue) throws -> [UInt8] {
        let colorDescription = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: .bgra8Unorm_srgb, width: size, height: size, mipmapped: false)
        colorDescription.storageMode = .shared
        colorDescription.usage = .renderTarget
        let depthDescription = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: .depth32Float, width: size, height: size, mipmapped: false)
        depthDescription.storageMode = .private
        depthDescription.usage = .renderTarget
        guard let color = device.makeTexture(descriptor: colorDescription),
              let depth = device.makeTexture(descriptor: depthDescription),
              let command = queue.makeCommandBuffer() else {
            throw RendererCheckFailure(message: "Cannot allocate bounded Metal check resources")
        }
        let pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = color
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].storeAction = .store
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        pass.depthAttachment.texture = depth
        pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.storeAction = .dontCare
        pass.depthAttachment.clearDepth = 1
        guard renderer.encodeScene(commandBuffer: command, renderPass: pass,
            drawableSize: CGSize(width: size, height: size)) else {
            throw RendererCheckFailure(message: "The production renderer did not encode its offscreen pass")
        }
        command.commit()
        command.waitUntilCompleted()
        guard command.status == .completed else {
            throw RendererCheckFailure(message: command.error?.localizedDescription ?? "Metal command failed")
        }
        var pixels = [UInt8](repeating: 0, count: size * size * 4)
        pixels.withUnsafeMutableBytes { bytes in
            color.getBytes(bytes.baseAddress!, bytesPerRow: size * 4,
                from: MTLRegionMake2D(0, 0, size, size), mipmapLevel: 0)
        }
        return pixels
    }

    mutating func run() throws {
        guard let device = MTLCreateSystemDefaultDevice(), device.hasUnifiedMemory,
              let queue = device.makeCommandQueue() else {
            throw RendererCheckFailure(message: "Checks require the local unified-memory Metal GPU")
        }
        print("Offscreen checks on \(device.name): 256 × 256, one sample per pixel.")
        let cached = try ReservoirMetalRenderer(device: device, sampleCount: 1)
        var state = ReservoirSceneState(mode: .fill, fillPct: 58, points: [], selectedIndex: 0,
            referenceRadius: 1, cutaway: true, showBands: true, spectralValues: [],
            zoneThresholds: [58, 62, 68, 71.5, 72, 74, 78, 82], selectedZonePct: 68,
            zoneShelfBounds: [58, 72])
        cached.update(state)
        var cases: [(ReservoirSceneState, Bool, String)] = []
        state.fillPct = 76
        cases.append((state, false, "A changed fill reuses references without retaining the old surface"))
        state.fillPct = 70; state.cutaway = false; state.showBands = false
        cases.append((state, false, "Cutaway and reference visibility changes invalidate fixed fill geometry"))
        state.cutaway = true; state.showBands = true
        cases.append((state, false, "Restoring fill styles reproduces a newly constructed renderer"))
        state.mode = .zones; state.fillPct = 73; state.cutaway = false
        cases.append((state, false, "Switching into Reference Zones discards the fill-view cache"))
        state.fillPct = 60
        cases.append((state, false, "A new zone fill preserves the exact fixed reference pixels"))
        state.selectedZonePct = 72
        cases.append((state, false, "Selecting another zone rebuilds its highlight and annotation boundary"))
        state.zoneThresholds = [55, 63, 69, 70, 76, 80]; state.zoneShelfBounds = [55, 70]
        state.selectedZonePct = 63
        cases.append((state, false, "Changed shelf and threshold inputs do not reuse obsolete boundaries"))
        state.fillPct = 52
        cases.append((state, false, "A fill outside the crop leaves no stale surface behind"))
        state.fillPct = 68
        cases.append((state, true, "Enabling the measured marker produces the same pixels as a fresh renderer"))
        cases.append((state, false, "Disabling the measured marker removes its pixels without changing references"))

        for (state, marker, description) in cases {
            try autoreleasepool {
                cached.update(state, smoothFill: marker)
                let fresh = try ReservoirMetalRenderer(device: device, sampleCount: 1)
                fresh.update(state, smoothFill: marker)
                let actual = try render(cached, device: device, queue: queue)
                let expected = try render(fresh, device: device, queue: queue)
                let background = Array(expected.prefix(4))
                let hasGeometry = stride(from: 4, to: expected.count, by: 4).contains {
                    Array(expected[$0..<($0 + 4)]) != background
                }
                try check(hasGeometry && actual == expected, description)
            }
        }

        // This view has no window, delegate, or event-loop run. It verifies the
        // production mode flags without opening or drawing into the user's app.
        let view = MTKView(frame: .zero, device: device)
        view.colorPixelFormat = .bgra8Unorm_srgb
        view.depthStencilPixelFormat = .depth32Float
        view.sampleCount = 1
        let attached = try ReservoirMetalRenderer(view: view)
        defer { view.isPaused = true }
        state.mode = .zones; state.fillPct = 58
        attached.update(state, smoothFill: true, animated: true, context: "health/1", sourceTime: 1)
        try check(view.isPaused && view.enableSetNeedsDisplay, "The first observation uses event-driven drawing")
        state.fillPct = 78
        attached.update(state, smoothFill: true, animated: true, context: "health/1", sourceTime: 2)
        try check(!view.isPaused && !view.enableSetNeedsDisplay, "An eased transition selects Metal's timed drawing mode")
        attached.update(state, smoothFill: true, animated: true, context: "health/1", sourceTime: 2)
        try check(!view.isPaused && !view.enableSetNeedsDisplay, "A duplicate observation keeps the active draw mode")
        attached.update(state, smoothFill: false, animated: true, context: "health/1", sourceTime: 2)
        try check(view.isPaused && view.enableSetNeedsDisplay, "Disabling smoothing immediately returns to event-driven drawing")
        state.fillPct = 62
        attached.update(state, smoothFill: true, animated: true, context: "health/1", sourceTime: 3)
        attached.update(state, smoothFill: true, animated: false, context: "health/1", sourceTime: 3)
        try check(view.isPaused && view.enableSetNeedsDisplay, "A stale or nonanimated update stops the timed loop")
        state.fillPct = 70
        attached.update(state, smoothFill: true, animated: true, context: "health/2", sourceTime: 1)
        try check(view.isPaused && view.enableSetNeedsDisplay, "A source-context switch snaps and keeps the timed loop stopped")
        state.fillPct = 76
        attached.update(state, smoothFill: true, animated: true, context: "health/2", sourceTime: 2)
        Thread.sleep(forTimeInterval: FillTransition.duration + 0.05)
        attached.update(state, smoothFill: true, animated: true, context: "health/2", sourceTime: 2)
        try check(view.isPaused && view.enableSetNeedsDisplay, "After its finite duration, an unchanged observation leaves drawing paused")
        print("\(passed) fill renderer checks passed; 20 bounded offscreen render commands completed.")
    }
}

do {
    var checks = FillRendererChecks()
    try checks.run()
} catch {
    FileHandle.standardError.write(Data("FAIL: \(error.localizedDescription)\n".utf8))
    exit(1)
}
