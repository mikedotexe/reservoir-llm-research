import Foundation
import Metal
import CryptoKit
import Darwin

/// A bounded rendering experiment that uses the viewer's own geometry and
/// encoder. It never starts the live reader, creates a window, or contacts a host.
enum ReservoirProfiler {
    static func runIfRequested(arguments: [String] = CommandLine.arguments) -> Bool {
        guard arguments.contains("--profile") else { return false }
        do {
            let options = try ProfileOptions(arguments: arguments)
            let report = try run(options: options)
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
            let data = try encoder.encode(report)
            if let output = options.output {
                try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true)
                try data.write(to: output, options: .atomic)
            }
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
            Darwin.exit(EXIT_SUCCESS)
        } catch {
            FileHandle.standardError.write(Data("Reservoir Scope profile failed: \(error.localizedDescription)\n".utf8))
            Darwin.exit(EXIT_FAILURE)
        }
    }

    private static func run(options: ProfileOptions) throws -> ProfileReport {
        let startedAt = ISO8601DateFormatter().string(from: Date())
        let environmentBefore = ProfileEnvironment.current()
        try requireCoolEnough()
        guard let device = MTLCreateSystemDefaultDevice(), let queue = device.makeCommandQueue() else {
            throw ProfileError("No Metal device and command queue are available in this session.")
        }
        let evidence = try EvidenceStore.load()
        let sampleCount = device.supportsTextureSampleCount(4) ? 4 : 1
        let allocatedBefore = device.currentAllocatedSize
        let compileStart = ProcessInfo.processInfo.systemUptime
        let renderer = try ReservoirMetalRenderer(device: device, sampleCount: sampleCount)
        let pipelineConstructionMs = (ProcessInfo.processInfo.systemUptime - compileStart) * 1000
        let targets = try ProfileTargets(device: device, width: options.width, height: options.height, sampleCount: sampleCount)
        let points = evidence.geometry.samples.map(\.pc)
        let spectrumScale = max(1, evidence.historical.samples.flatMap(\.cascade).max().map(sqrt) ?? 1)
        let bands = evidence.historical.bands
        let thresholds = ReferenceZone.catalog(bands: bands, configuration: evidence.historical.controller.structuralConfig).map(\.thresholdPct)
        let measuredStart = ProcessInfo.processInfo.systemUptime
        var peakAllocated = device.currentAllocatedSize
        var scenes: [ProfileSceneReport] = []

        for mode in [ReservoirSceneMode.fill, .zones, .trajectory, .spectral] {
            var frames: [ProfileFrame] = []
            for ordinal in 0..<(options.warmups + options.frames) {
                try requireCoolEnough()
                guard ProcessInfo.processInfo.systemUptime - measuredStart < 20 else {
                    throw ProfileError("The bounded 20-second rendering budget was reached. No successful report was written.")
                }
                let measuredOrdinal = ordinal - options.warmups
                let count = measuredOrdinal < 0 ? options.warmups : options.frames
                let sequenceOrdinal = measuredOrdinal < 0 ? ordinal : measuredOrdinal
                let historicalIndex = sampleIndex(ordinal: sequenceOrdinal, count: count, samples: evidence.historical.samples.count)
                let stateIndex = sampleIndex(ordinal: sequenceOrdinal, count: count, samples: points.count)
                let sample = evidence.historical.samples[historicalIndex]
                let state = ReservoirSceneState(mode: mode, fillPct: sample.fillPct, points: points,
                    selectedIndex: stateIndex,
                    referenceRadius: mode == .trajectory ? evidence.geometry.pca.normalization.referenceRadius : spectrumScale,
                    cutaway: mode == .fill, showBands: true, spectralValues: sample.cascade,
                    zoneThresholds: thresholds, selectedZonePct: bands.targetPct,
                    zoneShelfBounds: [bands.shelfMinPct, bands.shelfMaxPct])
                let frame = try autoreleasepool { () throws -> ProfileFrame in
                    let frameStart = ProcessInfo.processInfo.systemUptime
                    renderer.update(state)
                    let updatedAt = ProcessInfo.processInfo.systemUptime
                    guard let command = queue.makeCommandBuffer() else { throw ProfileError("A Metal command buffer could not be created.") }
                    command.label = "ReservoirScope profile \(mode.rawValue) \(ordinal)"
                    guard renderer.encodeScene(commandBuffer: command, renderPass: targets.pass,
                        drawableSize: CGSize(width: options.width, height: options.height)) else {
                        throw ProfileError("The shared scene encoder did not encode a render pass.")
                    }
                    command.commit()
                    let committedAt = ProcessInfo.processInfo.systemUptime
                    command.waitUntilCompleted()
                    let completedAt = ProcessInfo.processInfo.systemUptime
                    peakAllocated = max(peakAllocated, device.currentAllocatedSize)
                    guard command.status == .completed else {
                        throw ProfileError(command.error?.localizedDescription ?? "The Metal command did not complete successfully.")
                    }
                    // Apple specifies that these timestamps are valid only
                    // after completion. Missing/zero timestamps stay unknown.
                    let start = command.gpuStartTime, end = command.gpuEndTime
                    let gpuMs: Double? = start.isFinite && end.isFinite && start > 0 && end >= start ? (end - start) * 1000 : nil
                    return ProfileFrame(ordinal: max(0, measuredOrdinal), historicalRowIndex: historicalIndex,
                        stateRowIndex: stateIndex, drawCount: renderer.drawCount, vertexCount: renderer.vertexCount,
                        geometryBufferBytes: renderer.bufferBytes, cpuUpdateMs: (updatedAt - frameStart) * 1000,
                        cpuEncodeSubmitMs: (committedAt - updatedAt) * 1000,
                        gpuCommandMs: gpuMs, waitWallMs: (completedAt - committedAt) * 1000,
                        serialFrameWallMs: (completedAt - frameStart) * 1000)
                }
                if measuredOrdinal >= 0 { frames.append(frame) }
            }
            scenes.append(ProfileSceneReport(mode: mode.rawValue, frames: frames))
        }

        return ProfileReport(schemaVersion: "reservoir-scope-profile-v1", status: "completed",
            startedAtUTC: startedAt, completedAtUTC: ISO8601DateFormatter().string(from: Date()),
            device: ProfileDevice(name: device.name, hasUnifiedMemory: device.hasUnifiedMemory,
                recommendedMaxWorkingSetBytes: device.recommendedMaxWorkingSetSize,
                physicalMemoryBytes: ProcessInfo.processInfo.physicalMemory,
                cpuDescription: sysctlString("machdep.cpu.brand_string") ?? "unavailable",
                hardwareModel: sysctlString("hw.model") ?? "unavailable"),
            environmentBefore: environmentBefore, environmentAfter: .current(),
            workload: ProfileWorkload(widthPixels: options.width, heightPixels: options.height,
                sampleCount: sampleCount, warmupsPerScene: options.warmups, measuredFramesPerScene: options.frames,
                historicalSampleCount: evidence.historical.samples.count, stateSampleCount: points.count,
                elapsedRenderingWorkMs: (ProcessInfo.processInfo.systemUptime - measuredStart) * 1000,
                pipelineConstructionMs: pipelineConstructionMs),
            provenance: try ProfileProvenance.capture(sourceDirectory: options.sourceDirectory),
            memory: ProfileMemory(allocatedBeforeRendererBytes: allocatedBefore,
                peakSampledMetalResourceBytes: peakAllocated, allocatedAtEndBytes: device.currentAllocatedSize),
            scenes: scenes,
            limitations: [
                "Offscreen render passes reuse the native viewer's geometry, shaders, camera and draw encoder; no drawable is presented.",
                "Frames run serially and wait for completion. These durations do not measure display FPS, SwiftUI layout, compositing, input latency, idle cost, or energy.",
                "Recorded sample selection spans each bundled capture deterministically; the two captures are not synchronized observations.",
                "CPU update includes scene comparison, geometry generation, and immutable shared-buffer creation. Evidence decoding, target allocation and pipeline compilation are excluded from frame summaries.",
                "Metal resource allocation is sampled from this device object; it is not total app RSS, system memory pressure, or measured memory bandwidth.",
                "The workload uses Metal GPU rendering and CPU geometry. No Neural Engine work or live-system access occurs.",
                "Thermal and low-power states are snapshots. Other host activity is uncontrolled; this short run is not a sustained thermal or hardware throughput benchmark."
            ])
    }

    private static func sampleIndex(ordinal: Int, count: Int, samples: Int) -> Int {
        count <= 1 ? 0 : ordinal * (samples - 1) / (count - 1)
    }

    private static func requireCoolEnough() throws {
        let state = ProcessInfo.processInfo.thermalState
        guard state != .serious && state != .critical else {
            throw ProfileError("The host reports serious or critical thermal pressure; the optional profile stopped.")
        }
    }
}

private struct ProfileOptions {
    var width = 1280
    var height = 800
    var warmups = 8
    var frames = 30
    var output: URL?
    var sourceDirectory: URL?

    init(arguments: [String]) throws {
        var cursor = 1
        while cursor < arguments.count {
            let flag = arguments[cursor]
            if flag == "--profile" { cursor += 1; continue }
            guard cursor + 1 < arguments.count else { throw ProfileError("Missing value after \(flag).") }
            let value = arguments[cursor + 1]
            switch flag {
            case "--profile-width": width = try Self.boundedInt(value, range: 320...2560, name: flag)
            case "--profile-height": height = try Self.boundedInt(value, range: 240...1600, name: flag)
            case "--profile-warmups": warmups = try Self.boundedInt(value, range: 0...20, name: flag)
            case "--profile-frames": frames = try Self.boundedInt(value, range: 1...120, name: flag)
            case "--profile-output": output = URL(fileURLWithPath: value)
            case "--profile-source-directory": sourceDirectory = URL(fileURLWithPath: value, isDirectory: true)
            default: throw ProfileError("Unknown profiling option: \(flag).")
            }
            cursor += 2
        }
    }

    private static func boundedInt(_ text: String, range: ClosedRange<Int>, name: String) throws -> Int {
        guard let value = Int(text), range.contains(value) else { throw ProfileError("\(name) must be an integer in \(range).") }
        return value
    }
}

private struct ProfileTargets {
    let pass: MTLRenderPassDescriptor

    init(device: MTLDevice, width: Int, height: Int, sampleCount: Int) throws {
        func texture(format: MTLPixelFormat, samples: Int, name: String) throws -> MTLTexture {
            let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: format, width: width, height: height, mipmapped: false)
            descriptor.textureType = samples > 1 ? .type2DMultisample : .type2D
            descriptor.sampleCount = samples
            descriptor.storageMode = .private
            descriptor.usage = .renderTarget
            guard let texture = device.makeTexture(descriptor: descriptor) else { throw ProfileError("Could not allocate \(name) render target.") }
            texture.label = "ReservoirScope profile \(name)"
            return texture
        }
        let color = try texture(format: .bgra8Unorm_srgb, samples: sampleCount, name: "color")
        let depth = try texture(format: .depth32Float, samples: sampleCount, name: "depth")
        let pass = MTLRenderPassDescriptor()
        pass.colorAttachments[0].texture = color
        pass.colorAttachments[0].loadAction = .clear
        pass.colorAttachments[0].clearColor = MTLClearColor(red: 0.009, green: 0.017, blue: 0.031, alpha: 1)
        if sampleCount > 1 {
            pass.colorAttachments[0].resolveTexture = try texture(format: .bgra8Unorm_srgb, samples: 1, name: "resolve")
            pass.colorAttachments[0].storeAction = .multisampleResolve
        } else {
            pass.colorAttachments[0].storeAction = .store
        }
        pass.depthAttachment.texture = depth
        pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.clearDepth = 1
        pass.depthAttachment.storeAction = .dontCare
        self.pass = pass
    }
}

private struct ProfileError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

private struct ProfileReport: Encodable {
    let schemaVersion: String
    let status: String
    let startedAtUTC: String
    let completedAtUTC: String
    let device: ProfileDevice
    let environmentBefore: ProfileEnvironment
    let environmentAfter: ProfileEnvironment
    let workload: ProfileWorkload
    let provenance: ProfileProvenance
    let memory: ProfileMemory
    let scenes: [ProfileSceneReport]
    let limitations: [String]
}

private struct ProfileDevice: Encodable {
    let name: String
    let hasUnifiedMemory: Bool
    let recommendedMaxWorkingSetBytes: UInt64
    let physicalMemoryBytes: UInt64
    let cpuDescription: String
    let hardwareModel: String
}

private struct ProfileEnvironment: Encodable {
    let osVersion: String
    let processorCount: Int
    let activeProcessorCount: Int
    let thermalState: String
    let lowPowerModeEnabled: Bool

    static func current() -> Self {
        let process = ProcessInfo.processInfo
        let thermal: String
        switch process.thermalState {
        case .nominal: thermal = "nominal"
        case .fair: thermal = "fair"
        case .serious: thermal = "serious"
        case .critical: thermal = "critical"
        @unknown default: thermal = "unknown"
        }
        return Self(osVersion: process.operatingSystemVersionString, processorCount: process.processorCount,
            activeProcessorCount: process.activeProcessorCount, thermalState: thermal,
            lowPowerModeEnabled: process.isLowPowerModeEnabled)
    }
}

private struct ProfileWorkload: Encodable {
    let widthPixels: Int
    let heightPixels: Int
    let sampleCount: Int
    let warmupsPerScene: Int
    let measuredFramesPerScene: Int
    let historicalSampleCount: Int
    let stateSampleCount: Int
    let elapsedRenderingWorkMs: Double
    let pipelineConstructionMs: Double
    let colorFormat = "bgra8Unorm_srgb"
    let depthFormat = "depth32Float"
    let workloadVersion = "four-scenes-fixed-camera-v1"
    let sampling = "floor(ordinal * (sampleCount - 1) / (frameCount - 1)); warmup and measurement each span full capture"
    let camera = "Viewer default yaw -0.42, pitch 0.16, distance 3.8; zones use the native fixed orthographic lens"
    let geometry = "All bundled frozen PCA points supplied; fill cutaway and reference bands enabled; zones select configured target"
    let percentileMethod = "Sorted linear interpolation at (n - 1) * p; p95 is descriptive within this bounded run"
}

private struct ProfileMemory: Encodable {
    let allocatedBeforeRendererBytes: Int
    let peakSampledMetalResourceBytes: Int
    let allocatedAtEndBytes: Int
}

private struct ProfileProvenance: Encodable {
    struct FileDigest: Encodable {
        let name: String
        let bytes: Int
        let sha256: String
    }
    let appVersion: String
    let appBuild: String
    let executable: FileDigest
    let resources: [FileDigest]
    let sourceFiles: [FileDigest]?

    static func capture(sourceDirectory: URL?) throws -> Self {
        guard let executableURL = Bundle.main.executableURL else { throw ProfileError("Cannot identify this executable for hashing.") }
        var resources: [FileDigest] = []
        for name in ["data", "state-geometry"] {
            guard let url = Bundle.module.url(forResource: name, withExtension: "json")
                ?? Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Resources") else {
                throw ProfileError("Cannot identify bundled \(name).json for hashing.")
            }
            resources.append(try digest(url))
        }
        let sourceFiles: [FileDigest]?
        if let sourceDirectory {
            sourceFiles = try FileManager.default.contentsOfDirectory(at: sourceDirectory, includingPropertiesForKeys: nil)
                .filter { $0.pathExtension == "swift" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
                .map { try digest($0) }
        } else { sourceFiles = nil }
        return Self(appVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unavailable",
            appBuild: Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "unavailable",
            executable: try digest(executableURL), resources: resources, sourceFiles: sourceFiles)
    }

    private static func digest(_ url: URL) throws -> FileDigest {
        let data = try Data(contentsOf: url)
        return FileDigest(name: url.lastPathComponent, bytes: data.count,
            sha256: SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined())
    }
}

private struct ProfileFrame: Encodable {
    let ordinal: Int
    let historicalRowIndex: Int
    let stateRowIndex: Int
    let drawCount: Int
    let vertexCount: Int
    let geometryBufferBytes: Int
    let cpuUpdateMs: Double
    let cpuEncodeSubmitMs: Double
    let gpuCommandMs: Double?
    let waitWallMs: Double
    let serialFrameWallMs: Double
}

private struct ProfileSceneReport: Encodable {
    let mode: String
    let cpuUpdateMs: ProfileDistribution
    let cpuEncodeSubmitMs: ProfileDistribution
    let gpuCommandMs: ProfileDistribution
    let waitWallMs: ProfileDistribution
    let serialFrameWallMs: ProfileDistribution
    let frames: [ProfileFrame]

    init(mode: String, frames: [ProfileFrame]) {
        self.mode = mode
        self.frames = frames
        cpuUpdateMs = ProfileDistribution(frames.map(\.cpuUpdateMs))
        cpuEncodeSubmitMs = ProfileDistribution(frames.map(\.cpuEncodeSubmitMs))
        gpuCommandMs = ProfileDistribution(frames.compactMap(\.gpuCommandMs))
        waitWallMs = ProfileDistribution(frames.map(\.waitWallMs))
        serialFrameWallMs = ProfileDistribution(frames.map(\.serialFrameWallMs))
    }
}

private struct ProfileDistribution: Encodable {
    let count: Int
    let min: Double?
    let median: Double?
    let p95: Double?
    let max: Double?

    init(_ values: [Double]) {
        let sorted = values.sorted()
        count = sorted.count
        min = sorted.first
        max = sorted.last
        func percentile(_ p: Double) -> Double? {
            guard !sorted.isEmpty else { return nil }
            let position = Double(sorted.count - 1) * p
            let lower = Int(floor(position)), upper = Int(ceil(position))
            return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - Double(lower))
        }
        median = percentile(0.5)
        p95 = percentile(0.95)
    }
}

private func sysctlString(_ name: String) -> String? {
    var size = 0
    guard sysctlbyname(name, nil, &size, nil, 0) == 0, size > 0, size < 4096 else { return nil }
    var bytes = [CChar](repeating: 0, count: size)
    guard sysctlbyname(name, &bytes, &size, nil, 0) == 0 else { return nil }
    return String(cString: bytes)
}
