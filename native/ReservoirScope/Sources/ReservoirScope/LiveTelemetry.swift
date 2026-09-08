import Foundation
import Combine

/// An explicitly enabled, bounded, read-only view of health.json. Poll time is
/// never used as the source measurement time. This does not command the engine.
@MainActor
final class LiveTelemetryMonitor: ObservableObject {
    @Published private(set) var isRunning = false
    @Published private(set) var statusText = "Stopped"
    @Published private(set) var lastError: String?
    @Published private(set) var lastPollAt: Date?
    @Published private(set) var samples: [LiveTelemetrySample] = []
    @Published private(set) var sourcePath: String?

    var latest: LiveTelemetrySample? { samples.last }
    var lastSourceDate: Date? { latest?.sourceDate }
    let sampleLimit = 300
    let staleAfterSeconds: TimeInterval = 12
    private let reader = ReadOnlyTelemetryReader()
    private var pollingTask: Task<Void, Never>?
    private var generation = UUID()

    func start(path: String, config: StructuralPIConfiguration) {
        stop()
        guard !path.isEmpty else {
            statusText = "No source path"
            lastError = "The bundled controller snapshot does not identify a readable health.json path."
            return
        }
        sourcePath = path
        samples.removeAll(keepingCapacity: true)
        lastPollAt = nil
        lastError = nil
        isRunning = true
        statusText = "Reading source…"
        let run = UUID()
        generation = run
        pollingTask = Task { [weak self, reader] in
            while !Task.isCancelled {
                let result: Result<LiveTelemetrySample, Error>
                do { result = .success(try await reader.read(path: path, config: config)) }
                catch { result = .failure(error) }
                guard let self, self.generation == run, self.isRunning, !Task.isCancelled else { return }
                self.lastPollAt = Date()
                switch result {
                case .success(let sample): self.accept(sample)
                case .failure(let error):
                    self.lastError = error.localizedDescription
                    self.statusText = "Source unavailable"
                }
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

    private func accept(_ sample: LiveTelemetrySample) {
        lastError = nil
        if let previous = samples.last, previous.sessionId == sample.sessionId {
            if previous.snapshotSequence == sample.snapshotSequence {
                let age = Date().timeIntervalSince(previous.sourceDate)
                statusText = age > staleAfterSeconds ? "Stale source · no new snapshot" : "Waiting for next source snapshot"
                return
            }
            if previous.snapshotSequence > sample.snapshotSequence {
                statusText = "Source sequence moved backwards"
                lastError = "Ignored sequence \(sample.snapshotSequence) after \(previous.snapshotSequence) in session \(sample.sessionId)."
                return
            }
            if sample.elapsedS < previous.elapsedS {
                statusText = "Source engine time moved backwards"
                lastError = "Ignored engine time \(sample.elapsedS) after \(previous.elapsedS) seconds in session \(sample.sessionId)."
                return
            }
            if sample.sourceDate < previous.sourceDate {
                statusText = "Source wall clock moved backwards"
                lastError = "Ignored a source timestamp earlier than the previous accepted snapshot in session \(sample.sessionId)."
                return
            }
        } else if let previous = samples.last, previous.sessionId != sample.sessionId {
            // Engine seconds restart with a session; never connect two sessions
            // with one chart segment or silently treat their clocks as shared.
            samples.removeAll(keepingCapacity: true)
        }
        samples.append(sample)
        if samples.count > sampleLimit { samples.removeFirst(samples.count - sampleLimit) }
        let age = Date().timeIntervalSince(sample.sourceDate)
        if age > staleAfterSeconds {
            statusText = "Stale source · observed \(Int(age)) seconds ago"
        } else if age < -5 {
            statusText = "Source clock is ahead of local clock"
        } else {
            statusText = "Reading live snapshots"
        }
    }
}

struct LiveTelemetrySample: Identifiable, Sendable {
    let sessionId: Int
    let snapshotSequence: Int
    let sourceDate: Date
    let receivedAt: Date
    let fillPct: Double
    let elapsedS: Double // Source engine time, not seconds since polling began.
    let sourceReportedFillRatePctPerS: Double?
    let esnLeak: Double? // health.json currently does not report this field.
    let esnCovLambda1: Double?
    let geomRel: Double?
    let stateRms: Double?
    let controller: ControllerSnapshot
    let sourcePath: String
    var id: String { "\(sessionId):\(snapshotSequence)" }
    var spectralValues: [Double] { [] } // Full spectral components are absent from health.json.
    var leak: Double? { esnLeak }
    var geomRadius: Double? { stateRms }
    var gate: Double? { controller.gate }
    var filter: Double? { controller.filter }
    var derived: DerivedPIContributions? { controller.derived }
}

private actor ReadOnlyTelemetryReader {
    private let maximumBytes = 2 * 1024 * 1024

    func read(path: String, config: StructuralPIConfiguration) throws -> LiveTelemetrySample {
        let url = URL(fileURLWithPath: path)
        let handle: FileHandle
        do { handle = try FileHandle(forReadingFrom: url) }
        catch { throw LiveTelemetryError.unreadable(path, error.localizedDescription) }
        defer { try? handle.close() }
        let data: Data
        do { data = try handle.read(upToCount: maximumBytes + 1) ?? Data() }
        catch { throw LiveTelemetryError.unreadable(path, error.localizedDescription) }
        guard !data.isEmpty else { throw LiveTelemetryError.invalid("health.json was empty during this read.") }
        guard data.count <= maximumBytes else { throw LiveTelemetryError.invalid("health.json exceeds the 2 MiB read limit.") }
        let health: HealthSnapshot
        do { health = try EvidenceStore.decoder().decode(HealthSnapshot.self, from: data) }
        catch { throw LiveTelemetryError.invalid("health.json could not be decoded: \(error.localizedDescription)") }
        let receivedAt = Date()
        guard let provenance = health.provenance,
              let sessionId = provenance.sessionId,
              let sequence = provenance.snapshotSequence,
              let elapsedS = provenance.engineTS, elapsedS.isFinite,
              let sourceDate = provenance.date else {
            throw LiveTelemetryError.invalid("health.json lacks explicit session_id, snapshot_sequence, engine_t_s, or wall_clock_unix_ms provenance; poll time cannot substitute for it.")
        }
        guard health.fillPct.isFinite, (0...100).contains(health.fillPct) else {
            throw LiveTelemetryError.invalid("Source fill_pct is outside its finite 0–100% range.")
        }
        let structural = health.stableCore?.structuralPi
        let derived = deriveStructuralContributions(structural, fillPct: health.fillPct, config: config)
        let source = EvidenceFile(path: path, sha256: nil, snapshotPath: nil,
                                  status: "Bounded read-only live health JSON; not a frozen file capture.", line: nil)
        let controller = ControllerSnapshot(
            tUtc: sourceDate.ISO8601Format(), capturedAtUtc: receivedAt.ISO8601Format(),
            source: source, provenance: provenance, observedFillPct: health.fillPct,
            mode: health.stableCore?.controllerMode, stage: health.stableCore?.stage,
            structuralPi: structural, gateFilterPi: health.pi, gate: health.gate,
            filter: health.filt, derived: derived,
            note: "Structural error/integral belong to the previous controller input; current source fill is the later estimate. This read has no measured leak coefficient or per-node state trajectory.")
        return LiveTelemetrySample(sessionId: sessionId, snapshotSequence: sequence,
            sourceDate: sourceDate, receivedAt: receivedAt, fillPct: health.fillPct, elapsedS: elapsedS,
            sourceReportedFillRatePctPerS: health.dfillDt, esnLeak: nil,
            esnCovLambda1: health.lambda1Esn, geomRel: health.geomRel,
            stateRms: health.esn?.hStateRms, controller: controller, sourcePath: path)
    }
}

/// Source-derived algebra, not a replay or logged P/I pair. Requires explicit
/// normal-path flags; recovery, reentry, missing flags, or changed targets yield nil.
func deriveStructuralContributions(_ state: StructuralPISnapshot?, fillPct: Double,
                                   config: StructuralPIConfiguration) -> DerivedPIContributions? {
    guard let state, state.active == true, state.recoveryImpulseActive == false,
          state.reentryActive == false, state.lowFillEscapeActive == false,
          let target = state.targetFillPct, let error = state.errorPct,
          let integral = state.integral,
          [target, error, integral, config.kp, config.ki, config.maxOutput, config.deadbandPct].allSatisfy(\.isFinite),
          abs(target - config.targetFillPct) < 0.001,
          (0...1).contains(integral) else { return nil }
    let normalizedError = min(1, max(0, (error - config.deadbandPct) / 20))
    let proportional = config.kp * normalizedError
    let integralContribution = config.ki * integral
    let inputFill = target + error
    return DerivedPIContributions(pTerm: proportional, iTerm: integralContribution,
        piOutput: min(config.maxOutput, max(0, proportional + integralContribution)),
        controllerInputFillPct: inputFill, snapshotMinusControllerFillPct: fillPct - inputFill,
        status: "Derived from observed structural error/integral and bundled source constants. Loaded binary gains are not verified by this snapshot.",
        units: "Dimensionless controller contributions; fill error is percentage points.",
        note: "Drain policy and applied scaffold weights may override the raw PI output; generic gate/filter PI is a separate mechanism.")
}

private struct HealthSnapshot: Decodable, Sendable {
    let fillPct: Double
    let dfillDt: Double?
    let lambda1Esn: Double?
    let geomRel: Double?
    let gate: Double?
    let filt: Double?
    let provenance: TelemetryProvenance?
    let stableCore: HealthStableCore?
    let pi: GateFilterPISnapshot?
    let esn: HealthESN?
}

private struct HealthStableCore: Decodable, Sendable {
    let controllerMode: String?
    let stage: String?
    let structuralPi: StructuralPISnapshot?
}

private struct HealthESN: Decodable, Sendable {
    let hStateRms: Double?
}

enum LiveTelemetryError: LocalizedError, Sendable {
    case unreadable(String, String)
    case invalid(String)
    var errorDescription: String? {
        switch self {
        case .unreadable(let path, let reason): return "Cannot read \(path): \(reason)"
        case .invalid(let reason): return reason
        }
    }
}
