// Test adapter only. The desktop obtains this shape from the validated Rust core.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import type { GeometryEntry, GeometryPacket, GeometrySnapshot } from './geometryTypes';

export function geometryFixture(origin: GeometryPacket['origin'] = 'syntheticExample'): GeometryPacket {
  const bytes = readFileSync(new URL('../../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/minime-synthetic-geometry.json', import.meta.url));
  const envelope = JSON.parse(bytes.toString());
  const body = JSON.parse(envelope.body_json);
  const records: GeometryEntry[] = body.history.records.map((record: { id: string; request_id: string; request_sha256: string; body_json: string }) => {
    const entry = JSON.parse(record.body_json);
    const s = entry.snapshot;
    const snapshot: GeometrySnapshot | null = s ? {
      sourceSha256: s.source_sha256, capturedAtUnixMs: String(s.captured_at_unix_ms), requestedSeconds: s.requested_seconds,
      source: s.source, scope: s.scope, identity: s.identity, durationMs: s.frames.at(-1).t_ms - s.frames[0].t_ms,
      gaps: s.frames.slice(1).flatMap((f: { t_ms: number }, i: number) => f.t_ms - s.frames[i].t_ms > 1000 ? [[String(s.frames[i].t_ms), String(f.t_ms)]] : []),
      frames: s.frames.map((f: { t_ms: number; wall_clock_unix_ms: number; activations: number[] }) => ({ tMs: String(f.t_ms), wallClockUnixMs: String(f.wall_clock_unix_ms), activations: f.activations, rms: Math.sqrt(f.activations.reduce((sum, x) => sum + x * x, 0) / 128) })),
    } : null;
    return { id: record.id, requestId: record.request_id, requestSha256: record.request_sha256, kind: entry.kind,
      authoredText: entry.note ?? entry.expectation ?? entry.text ?? null, snapshot, baseline: entry.baseline ?? null,
      maximumRmsDistance: entry.maximum_rms_distance ?? null, prediction: entry.prediction ?? null, observation: entry.observation ?? null,
      recipe: entry.recipe ?? null, rmsDistance: entry.rms_distance ?? null, thresholdMet: entry.threshold_met ?? null, target: entry.target ?? null };
  });
  return { packetId: 'test-packet', filename: 'synthetic-geometry-example.json', origin, sha256: createHash('sha256').update(bytes).digest('hex'),
    bodySha256: envelope.body_sha256, sizeBytes: bytes.length, owner: body.owner, questionId: body.question_id, question: body.question,
    limits: body.limits, verificationScope: 'Test view contract; Rust independently validates canonical fixture bytes.', records };
}
