import Foundation
import Combine

/// Opt-in read-only projection of the producer's bounded activation recorder.
/// The recorder clocks identify observations, not engine steps or boot sessions.
/// A new batch replaces the previous batch; paths never bridge two file snapshots.
@MainActor
final class LiveStateMonitor: ObservableObject {
    @Published private(set) var isRunning = false
    @Published private(set) var statusText = "Stopped"
    @Published private(set) var lastError: String?
    @Published private(set) var lastPollAt: Date?
    @Published private(set) var samples: [LiveStateSample] = []
    @Published private(set) var sourcePath: String?
    @Published private(set) var continuityText = "No activation observations"

    var latest: LiveStateSample? { samples.last }
    var lastSourceDate: Date? { latest?.sourceDate }
    let sampleLimit = 180
    let staleAfterSeconds: TimeInterval = 12
    private let reader = ReadOnlyStateReader()
    private var pollingTask: Task<Void, Never>?
    private var generation = UUID()
    private var continuity = LiveStateContinuity()

    func start(path: String, basis: PrincipalComponents) {
        stop()
        sourcePath = path
        samples = []
        lastPollAt = nil
        lastError = nil
        continuity = LiveStateContinuity()
        continuityText = "No activation observations"
        do {
            guard !path.isEmpty else { throw LiveStateError.invalid("Choose an activation trace JSON file.") }
            try validateLiveStateBasis(basis)
        } catch {
            statusText = "Source unavailable"
            lastError = error.localizedDescription
            return
        }
        isRunning = true
        statusText = "Reading activations…"
        let run = UUID()
        generation = run
        pollingTask = Task { [weak self, reader] in
            while !Task.isCancelled {
                let result: Result<LiveStateBatch, Error>
                do { result = .success(try await reader.read(path: path, basis: basis)) }
                catch { result = .failure(error) }
                guard let self, self.generation == run, self.isRunning, !Task.isCancelled else { return }
                self.lastPollAt = Date()
                switch result {
                case .success(let batch): self.accept(batch)
                case .failure(let error): self.report(error)
                }
                // Read duration is additional to this delay, as with health polling.
                do { try await Task.sleep(for: .seconds(2)) }
                catch { return }
            }
        }
    }

    func stop() {
        generation = UUID()
        pollingTask?.cancel()
        pollingTask = nil
        isRunning = false
        statusText = "Stopped"
    }

    private func accept(_ batch: LiveStateBatch) {
        do {
            let disposition = try continuity.accept(batch)
            lastError = nil
            switch disposition {
            case .unchanged:
                updateFreshness(unchanged: true)
            case .replaced(let description):
                samples = batch.samples
                continuityText = description
                updateFreshness(unchanged: false)
            }
        } catch { report(error) }
    }

    private func updateFreshness(unchanged: Bool) {
        guard let sourceDate = latest?.sourceDate else { return }
        let age = Date().timeIntervalSince(sourceDate)
        if age > staleAfterSeconds {
            statusText = "Stale activation source · observed \(Int(age)) seconds ago"
        } else if age < -5 {
            statusText = "Activation source clock is ahead of local clock"
        } else {
            statusText = unchanged ? "Waiting for next activation batch" : "Reading live activation batches"
        }
    }

    private func report(_ error: Error) {
        lastError = error.localizedDescription
        statusText = samples.isEmpty ? "Source unavailable" : "Source unavailable · retaining stale batch"
    }
}

struct LiveStateSample: Identifiable, Sendable {
    let tMs: UInt64
    let wallClockUnixMs: UInt64
    let receivedAt: Date
    let fillPct: Double
    let stage: String
    let geomRel: Double
    let lambda1Rel: Double
    /// Exact values accepted from this recorder frame. Surface rendering must
    /// not reconstruct these from the three retained PCA scores.
    let activations: [Double]
    let geometry: StateGeometrySample
    var sourceDate: Date { Date(timeIntervalSince1970: Double(wallClockUnixMs) / 1000) }
    var elapsedS: Double { Double(tMs) / 1000 }
    var id: String { "recorder:\(tMs):\(wallClockUnixMs)" }
    var basisCompatibilityText: String {
        "128 coordinate positions match; node-layout identity with the frozen basis is unverified"
    }
    /// Fraction of this state's centered squared distance captured by the frozen
    /// axes. This is not explained variance across the incoming batch.
    var retainedDistanceFraction: Double? {
        guard geometry.centeredNorm > 0 else { return nil }
        return pow(geometry.projectedNorm / geometry.centeredNorm, 2)
    }
}

struct LiveStateBatch: Sendable {
    let samples: [LiveStateSample]
    fileprivate let sourceData: Data
    fileprivate let trace: ActivationTraceV1

    static func decode(data: Data, basis: PrincipalComponents, receivedAt: Date = Date()) throws -> Self {
        guard !data.isEmpty else { throw LiveStateError.invalid("The activation trace was empty during this read.") }
        guard data.count <= 2 * 1024 * 1024 else { throw LiveStateError.invalid("The activation trace exceeds the 2 MiB read limit.") }
        try validateLiveStateBasis(basis)
        let trace: ActivationTraceV1
        do { trace = try JSONDecoder().decode(ActivationTraceV1.self, from: data) }
        catch { throw LiveStateError.invalid("The activation trace could not be decoded: \(error.localizedDescription)") }
        guard trace.policy == "esn_activation_trace_v1", trace.reservoirDim == 128,
              trace.sampleIntervalMs == 1_000, trace.retainedSecs == 180 else {
            throw LiveStateError.invalid("Expected activation trace v1, 128 nodes, and the audited 1000 ms / 180-frame recorder policy.")
        }
        guard !trace.frames.isEmpty, trace.frames.count <= 180 else {
            throw LiveStateError.invalid("The activation trace must contain between 1 and 180 frames.")
        }
        guard trace.updatedAtUnixMs == trace.frames.last?.wallClockUnixMs else {
            throw LiveStateError.invalid("The activation batch update clock does not match its final frame.")
        }
        var previous: ActivationFrameV1?
        var samples: [LiveStateSample] = []
        samples.reserveCapacity(trace.frames.count)
        for (index, frame) in trace.frames.enumerated() {
            try frame.validate(index: index)
            if let previous {
                guard frame.tMs > previous.tMs, frame.wallClockUnixMs > previous.wallClockUnixMs,
                      frame.tMs - previous.tMs >= trace.sampleIntervalMs else {
                    throw LiveStateError.invalid("Activation frame \(index) duplicates or reverses a recorder clock, or violates the minimum sample interval.")
                }
            }
            previous = frame
            let centered = zip(frame.activations, basis.mean).map(-)
            let pc = basis.components.map { component in zip(centered, component).reduce(0) { $0 + $1.0 * $1.1 } }
            let centeredSquared = centered.reduce(0) { $0 + $1 * $1 }
            let projectedSquared = pc.reduce(0) { $0 + $1 * $1 }
            // Explicit residual vector avoids cancellation when a state lies in
            // the retained subspace. No clipping to the historical radius.
            let residualSquared = centered.indices.reduce(0.0) { total, node in
                let reconstructed = (0..<3).reduce(0.0) { $0 + pc[$1] * basis.components[$1][node] }
                let error = centered[node] - reconstructed
                return total + error * error
            }
            let stateSquared = frame.activations.reduce(0) { $0 + $1 * $1 }
            guard (pc + [centeredSquared, projectedSquared, residualSquared, stateSquared]).allSatisfy(\.isFinite) else {
                throw LiveStateError.invalid("Activation projection produced non-finite distances.")
            }
            let geometry = StateGeometrySample(index: index, pc: pc,
                stateRms: sqrt(stateSquared / 128), centeredRms: sqrt(centeredSquared / 128),
                projectedRms: sqrt(projectedSquared / 128), reconstructionRmse: sqrt(residualSquared / 128),
                centeredNorm: sqrt(centeredSquared), projectedNorm: sqrt(projectedSquared), residualNorm: sqrt(residualSquared))
            samples.append(LiveStateSample(tMs: frame.tMs, wallClockUnixMs: frame.wallClockUnixMs,
                receivedAt: receivedAt, fillPct: frame.fillPct, stage: frame.stage,
                geomRel: frame.geomRel, lambda1Rel: frame.lambda1Rel,
                activations: frame.activations, geometry: geometry))
        }
        return Self(samples: samples, sourceData: data, trace: trace)
    }
}

/// Recorder overlap is evidence about repeated file frames only. It cannot
/// establish boot identity or whether node order matches the frozen PCA basis.
struct LiveStateContinuity {
    private(set) var accepted: LiveStateBatch?

    mutating func accept(_ batch: LiveStateBatch) throws -> LiveStateBatchDisposition {
        guard let previous = accepted else {
            accepted = batch
            return .replaced("First bounded batch · boot and node-layout identity unavailable")
        }
        if batch.sourceData == previous.sourceData { return .unchanged }
        let oldLast = previous.trace.frames.last!
        let newLast = batch.trace.frames.last!
        guard newLast.wallClockUnixMs > oldLast.wallClockUnixMs else {
            throw LiveStateError.invalid(newLast.wallClockUnixMs == oldLast.wallClockUnixMs
                ? "Activation contents changed without a new source clock; retaining the previous batch."
                : "Activation source wall time moved backwards; retaining the previous batch.")
        }
        if newLast.tMs < oldLast.tMs {
            accepted = batch
            return .replaced("Recorder clock restarted · boot identity unverified; batch replaced")
        }
        guard newLast.tMs > oldLast.tMs else {
            throw LiveStateError.invalid("Activation contents changed at the same recorder time; retaining the previous batch.")
        }
        let oldFrames = Dictionary(uniqueKeysWithValues: previous.trace.frames.map { ($0.tMs, $0) })
        var overlap = 0
        for frame in batch.trace.frames {
            if let oldFrame = oldFrames[frame.tMs] {
                guard frame == oldFrame else {
                    throw LiveStateError.invalid("An overlapping activation frame changed at a previously observed recorder time; retaining the previous batch.")
                }
                overlap += 1
            }
        }
        accepted = batch
        return .replaced(overlap > 0
            ? "\(overlap) unchanged overlapping frames · batch replaced; boot identity unverified"
            : "No observed overlap · batch replaced; continuity and boot identity unverified")
    }
}

enum LiveStateBatchDisposition {
    case unchanged
    case replaced(String)
}

func validateLiveStateBasis(_ basis: PrincipalComponents) throws {
    guard basis.frozen == true, basis.dimensions == 128, basis.mean.count == 128,
          basis.mean.allSatisfy(\.isFinite), basis.components.count == 3,
          basis.components.allSatisfy({ $0.count == 128 && $0.allSatisfy(\.isFinite) }),
          basis.normalization.referenceRadius.isFinite, basis.normalization.referenceRadius > 0 else {
        throw LiveStateError.invalid("Live geometry requires a frozen finite 128-node mean, three matching PCA axes, and a positive reference radius.")
    }
    for row in 0..<3 {
        for other in 0...row {
            let dot = zip(basis.components[row], basis.components[other]).reduce(0.0) { $0 + $1.0 * $1.1 }
            guard abs(dot - (row == other ? 1 : 0)) <= 1e-6 else {
                throw LiveStateError.invalid("The frozen PCA axes are not orthonormal; live projection is unavailable.")
            }
        }
    }
}

private actor ReadOnlyStateReader {
    private let maximumBytes = 2 * 1024 * 1024
    func read(path: String, basis: PrincipalComponents) throws -> LiveStateBatch {
        let handle: FileHandle
        do { handle = try FileHandle(forReadingFrom: URL(fileURLWithPath: path)) }
        catch { throw LiveStateError.invalid("Cannot read \(path): \(error.localizedDescription)") }
        defer { try? handle.close() }
        let data = try handle.read(upToCount: maximumBytes + 1) ?? Data()
        return try LiveStateBatch.decode(data: data, basis: basis)
    }
}

fileprivate struct ActivationTraceV1: Decodable, Sendable {
    let policy: String
    let updatedAtUnixMs: UInt64
    let reservoirDim: Int
    let sampleIntervalMs: UInt64
    let retainedSecs: UInt64
    let frames: [ActivationFrameV1]
    enum CodingKeys: String, CodingKey {
        case policy, frames
        case updatedAtUnixMs = "updated_at_unix_ms", reservoirDim = "reservoir_dim"
        case sampleIntervalMs = "sample_interval_ms", retainedSecs = "retained_secs"
    }
}

fileprivate struct ActivationFrameV1: Decodable, Sendable, Equatable {
    let tMs: UInt64
    let wallClockUnixMs: UInt64
    let fillPct: Double
    let stage: String
    let geomRel: Double
    let lambda1Rel: Double
    let summary: ActivationSummaryV1
    let topActiveNodeIndexes: [Int]
    let activations: [Double]
    enum CodingKeys: String, CodingKey {
        case stage, summary, activations
        case tMs = "t_ms", wallClockUnixMs = "wall_clock_unix_ms", fillPct = "fill_pct"
        case geomRel = "geom_rel", lambda1Rel = "lambda1_rel", topActiveNodeIndexes = "top_active_node_indexes"
    }

    func validate(index: Int) throws {
        guard wallClockUnixMs > 0, wallClockUnixMs <= 253_402_300_799_999,
              fillPct.isFinite, (0...100).contains(fillPct), !stage.isEmpty, stage.count <= 128,
              geomRel.isFinite, geomRel >= 0, lambda1Rel.isFinite, lambda1Rel >= 0,
              activations.count == 128, activations.allSatisfy({ $0.isFinite && (-1...1).contains($0) }),
              topActiveNodeIndexes.count == 8, Set(topActiveNodeIndexes).count == 8,
              topActiveNodeIndexes.allSatisfy({ (0..<128).contains($0) }), summary.isValid else {
            throw LiveStateError.invalid("Activation frame \(index) has invalid clocks, dimensions, values, or a sanitized/non-finite activation summary.")
        }
    }
}

fileprivate struct ActivationSummaryV1: Decodable, Sendable, Equatable {
    let mean: Double
    let absMean: Double
    let rms: Double
    let min: Double
    let max: Double
    let saturationFraction: Double
    let positiveFraction: Double
    let finiteFraction: Double
    enum CodingKeys: String, CodingKey {
        case mean, rms, min, max
        case absMean = "abs_mean", saturationFraction = "saturation_fraction"
        case positiveFraction = "positive_fraction", finiteFraction = "finite_fraction"
    }
    var isValid: Bool {
        [mean, absMean, rms, min, max, saturationFraction, positiveFraction, finiteFraction].allSatisfy(\.isFinite)
            && finiteFraction == 1 && (-1...1).contains(mean) && (-1...1).contains(min)
            && (-1...1).contains(max) && min <= max && (0...1).contains(absMean)
            && (0...1).contains(rms) && (0...1).contains(saturationFraction) && (0...1).contains(positiveFraction)
    }
}

enum LiveStateError: LocalizedError, Sendable {
    case invalid(String)
    var errorDescription: String? {
        switch self { case .invalid(let message): return message }
    }
}
