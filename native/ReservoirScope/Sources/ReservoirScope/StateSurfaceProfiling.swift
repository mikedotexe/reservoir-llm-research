import Foundation
import Metal
import CryptoKit
import Darwin

/// Fixed, finite offscreen workload. See docs/STATE-SURFACE-PROFILING.md.
/// No app window, live readers, remote connection or invented capture clock.
@MainActor enum StateSurfaceProfiler {
    static func runIfRequested(arguments: [String] = CommandLine.arguments) -> Bool {
        guard arguments.contains("--profile-surface") else { return false }
        do {
            let options = try SurfaceProfileOptions(arguments)
            let report = try run(options)
            let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
            if let output = options.output {
                try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true)
                try data.write(to: output, options: .atomic)
            }
            FileHandle.standardOutput.write(data + Data("\n".utf8))
            Darwin.exit(EXIT_SUCCESS)
        } catch {
            FileHandle.standardError.write(Data("State surface profile failed: \(error.localizedDescription)\n".utf8))
            Darwin.exit(EXIT_FAILURE)
        }
    }

    private static func run(_ options: SurfaceProfileOptions) throws -> [String: Any] {
        let started = ISO8601DateFormatter().string(from: Date())
        let environmentBefore = environment()
        try thermalCheck()
        guard let device = MTLCreateSystemDefaultDevice() else { throw SurfaceRenderError("No Metal device is available.") }
        let evidence = try EvidenceStore.load()
        guard let replay = evidence.stateReplay else { throw SurfaceRenderError("The retained state replay resource is unavailable.") }
        let provenanceBefore = try provenance(options: options, replay: replay)
        let allocatedBefore = device.currentAllocatedSize
        let constructionStart = ProcessInfo.processInfo.systemUptime
        let sampleCount = device.supportsTextureSampleCount(4) ? 4 : 1
        let renderer = try StateSurfaceRenderer(device: device, sampleCount: sampleCount)
        let constructionMs = (ProcessInfo.processInfo.systemUptime - constructionStart) * 1000
        let targets = try SurfaceProfileTargets(device: device, sampleCount: sampleCount)
        var peakAllocated = device.currentAllocatedSize
        let renderStart = ProcessInfo.processInfo.systemUptime
        var cases: [[String: Any]] = []
        for scenario in [("signed_color", 0.0, false), ("signed_relief", 0.14, false), ("signed_relief_cutaway", 0.14, true)] {
            var frames: [[String: Any]] = []
            for ordinal in 0..<38 {
                try thermalCheck()
                guard ProcessInfo.processInfo.systemUptime - renderStart < 45 else {
                    throw SurfaceRenderError("The 45-second rendering limit was reached; no completed report was written.")
                }
                let measured = ordinal >= 8
                let phaseOrdinal = measured ? ordinal - 8 : ordinal
                let phaseCount = measured ? 30 : 8
                let index = phaseOrdinal * (replay.frames.count - 1) / (phaseCount - 1)
                let input = StateSurfaceRenderInput(values: replay.frames[index].activations,
                    lower: -1, upper: 1, fillPct: 68, relief: scenario.1, cutaway: scenario.2, selectedNode: 0)
                let record: [String: Any] = try autoreleasepool {
                    let start = ProcessInfo.processInfo.systemUptime
                    let changed = try renderer.update(input)
                    let updated = ProcessInfo.processInfo.systemUptime
                    guard let command = renderer.queue.makeCommandBuffer() else { throw SurfaceRenderError("No Metal command buffer.") }
                    command.label = "State surface profile \(scenario.0) \(ordinal)"
                    guard renderer.encode(command: command, pass: targets.pass, size: CGSize(width: 1280, height: 800)) else {
                        throw SurfaceRenderError("The state surface render pass was not encoded.")
                    }
                    command.commit()
                    let committed = ProcessInfo.processInfo.systemUptime
                    command.waitUntilCompleted()
                    let completed = ProcessInfo.processInfo.systemUptime
                    guard command.status == .completed, let mesh = renderer.mesh else {
                        throw SurfaceRenderError(command.error?.localizedDescription ?? "The state surface command failed.")
                    }
                    guard completed - renderStart < 45 else {
                        throw SurfaceRenderError("The completed command exceeded the 45-second rendering budget; no completed report was written.")
                    }
                    peakAllocated = max(peakAllocated, device.currentAllocatedSize)
                    let gpuStart = command.gpuStartTime, gpuEnd = command.gpuEndTime
                    let gpu: Any = gpuStart.isFinite && gpuEnd.isFinite && gpuStart > 0 && gpuEnd >= gpuStart
                        ? (gpuEnd - gpuStart) * 1000 : NSNull()
                    return ["ordinal": phaseOrdinal, "stateRowIndex": index, "changedObservation": changed,
                        "vertexCount": renderer.vertexCount, "geometryBufferBytes": renderer.bufferBytes,
                        "requestedRelief": mesh.requestedRelief, "appliedRelief": mesh.appliedRelief,
                        "volumeError": abs(mesh.volume - mesh.targetVolume), "meshFallback": mesh.fallbackReason as Any? ?? NSNull(),
                        "cpuUpdateMs": (updated-start)*1000, "cpuEncodeSubmitMs": (committed-updated)*1000,
                        "gpuCommandMs": gpu, "waitWallMs": (completed-committed)*1000,
                        "serialFrameWallMs": (completed-start)*1000]
                }
                if measured { frames.append(record) }
            }
            cases.append(["mode": scenario.0, "requestedRelief": scenario.1, "cutaway": scenario.2, "frames": frames])
        }
        let elapsedRenderingMs = (ProcessInfo.processInfo.systemUptime-renderStart)*1000
        let provenanceAfter = try provenance(options: options, replay: replay)
        guard try JSONSerialization.data(withJSONObject: provenanceBefore, options: [.sortedKeys])
                == JSONSerialization.data(withJSONObject: provenanceAfter, options: [.sortedKeys]) else {
            throw SurfaceRenderError("Executable, source or evidence resources changed during the profile; no completed report was written.")
        }
        return ["schemaVersion": "reservoir-scope-state-surface-profile-v1", "status": "completed",
            "startedAtUTC": started, "completedAtUTC": ISO8601DateFormatter().string(from: Date()),
            "device": ["name": device.name, "hasUnifiedMemory": device.hasUnifiedMemory,
                "recommendedMaxWorkingSetBytes": device.recommendedMaxWorkingSetSize,
                "physicalMemoryBytes": ProcessInfo.processInfo.physicalMemory,
                "hardwareModel": sysctlString("hw.model") ?? "unavailable",
                "cpuDescription": sysctlString("machdep.cpu.brand_string") ?? "unavailable"],
            "environmentBefore": environmentBefore, "environmentAfter": environment(),
            "workload": ["widthPixels": 1280, "heightPixels": 800, "sampleCount": sampleCount,
                "warmupsPerScene": 8, "measuredFramesPerScene": 30, "caseCount": 3,
                "stateSampleCount": replay.frames.count, "stateDimensions": replay.dimensions,
                "previewFillPct": 68, "previewFillIsObserved": false, "lower": -1, "upper": 1,
                "showSites": true, "selectedNode": 0, "atlasVersion": StateSurfaceAtlas.version,
                "renderingBudgetSeconds": 45, "elapsedRenderingWorkMs": elapsedRenderingMs,
                "pipelineAndAtlasConstructionMs": constructionMs],
            "provenance": provenanceBefore,
            "memory": ["allocatedBeforeRendererBytes": allocatedBefore,
                "peakSampledMetalResourceBytes": peakAllocated, "allocatedAtEndBytes": device.currentAllocatedSize],
            "scenes": cases,
            "limitations": ["Offscreen native renderer workload; no drawable or window is presented.",
                "Serial completion waits do not measure display FPS, SwiftUI layout, compositing, input latency, idle cost or energy.",
                "68 percent fill is a fixed preview parameter. Retained states have no paired fill or per-row timestamps.",
                "CPU update includes checked volume-preserving geometry and immutable shared buffers; GPU evaluates the field and lighting.",
                "Evidence decoding, render targets and pipeline/atlas construction are excluded from frame intervals.",
                "Allocation snapshots are Metal resources on this device, not application RSS, memory pressure or measured bandwidth.",
                "No Neural Engine work or live-system access occurs. Host background work is uncontrolled."]]
    }

    private static func environment() -> [String: Any] {
        let info = ProcessInfo.processInfo
        let thermal: String
        switch info.thermalState {
        case .nominal: thermal = "nominal"
        case .fair: thermal = "fair"
        case .serious: thermal = "serious"
        case .critical: thermal = "critical"
        @unknown default: thermal = "unknown"
        }
        return ["osVersion": info.operatingSystemVersionString, "processorCount": info.processorCount,
                "activeProcessorCount": info.activeProcessorCount, "thermalState": thermal,
                "lowPowerModeEnabled": info.isLowPowerModeEnabled]
    }
    private static func thermalCheck() throws {
        let state = ProcessInfo.processInfo.thermalState
        guard state != .serious && state != .critical else { throw SurfaceRenderError("Serious or critical thermal pressure; profile stopped.") }
    }
    private static func hash(_ url: URL) throws -> String {
        SHA256.hash(data: try Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
    }
    private static func provenance(options: SurfaceProfileOptions, replay: StateReplayEvidence) throws -> [String: Any] {
        let executable = URL(fileURLWithPath: CommandLine.arguments[0]).standardizedFileURL
        var resources: [String: String] = [:]
        for name in ["data.json", "state-geometry.json", "state-replay.json", "state-replay.bin"] {
            let path = name as NSString
            guard let url = Bundle.module.url(forResource: path.deletingPathExtension, withExtension: path.pathExtension)
                    ?? Bundle.module.url(forResource: path.deletingPathExtension, withExtension: path.pathExtension, subdirectory: "Resources") else {
                throw SurfaceRenderError("Missing profiling resource: \(name)")
            }
            resources[name] = try hash(url)
        }
        var sources: [String: String] = [:]
        if let directory = options.sourceDirectory {
            for url in try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
                .filter({ $0.pathExtension == "swift" }).sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
                sources[url.lastPathComponent] = try hash(url)
            }
            guard !sources.isEmpty else { throw SurfaceRenderError("The supplied source directory contains no Swift files.") }
        }
        return ["executablePath": executable.path, "executableSHA256": try hash(executable),
            "resourceSHA256": resources, "sourceSHA256": sources,
            "sourceDirectory": options.sourceDirectory?.path as Any? ?? NSNull(),
            "sourceStatus": options.sourceDirectory == nil ? "Source directory not supplied; source hashes unavailable" : "Inspected supplied source files; executable identity recorded separately",
            "retainedActivationSHA256": replay.sourceSHA256, "frozenGeometrySHA256": replay.geometrySHA256,
            "basisCompatibility": replay.basisCompatibilityText]
    }
    private static func sysctlString(_ key: String) -> String? {
        var size = 0
        guard sysctlbyname(key, nil, &size, nil, 0) == 0, size > 0 else { return nil }
        var bytes = [CChar](repeating: 0, count: size)
        guard sysctlbyname(key, &bytes, &size, nil, 0) == 0 else { return nil }
        return String(cString: bytes)
    }
}

private struct SurfaceProfileOptions {
    var output: URL?
    var sourceDirectory: URL?
    init(_ arguments: [String]) throws {
        var i = 1
        while i < arguments.count {
            if arguments[i] == "--profile-surface" { i += 1; continue }
            guard i + 1 < arguments.count else { throw SurfaceRenderError("Missing value after \(arguments[i]).") }
            switch arguments[i] {
            case "--profile-output": output = URL(fileURLWithPath: arguments[i+1])
            case "--profile-source-directory": sourceDirectory = URL(fileURLWithPath: arguments[i+1], isDirectory: true)
            default: throw SurfaceRenderError("Unknown state surface profiling option: \(arguments[i])")
            }
            i += 2
        }
    }
}

private struct SurfaceProfileTargets {
    let pass: MTLRenderPassDescriptor
    init(device: MTLDevice, sampleCount: Int) throws {
        func texture(_ format: MTLPixelFormat, _ samples: Int) throws -> MTLTexture {
            let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: format, width: 1280, height: 800, mipmapped: false)
            d.textureType = samples > 1 ? .type2DMultisample : .type2D
            d.sampleCount = samples; d.storageMode = .private; d.usage = .renderTarget
            guard let texture = device.makeTexture(descriptor: d) else { throw SurfaceRenderError("Failed to allocate offscreen state surface target.") }
            return texture
        }
        let pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = try texture(.bgra8Unorm_srgb, sampleCount)
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        if sampleCount > 1 {
            pass.colorAttachments[0].resolveTexture = try texture(.bgra8Unorm_srgb, 1)
            pass.colorAttachments[0].storeAction = .multisampleResolve
        } else { pass.colorAttachments[0].storeAction = .store }
        pass.depthAttachment.texture = try texture(.depth32Float, sampleCount)
        pass.depthAttachment.loadAction = .clear; pass.depthAttachment.clearDepth = 1; pass.depthAttachment.storeAction = .dontCare
        self.pass = pass
    }
}
