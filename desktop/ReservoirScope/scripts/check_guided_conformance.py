#!/usr/bin/env python3
"""Compare portable guide evidence with unchanged native Swift at retained cursors.

Offline: builds temporary Swift artifacts, reads canonical examples, and compares
exact state/wording/evidence steps. Deliberately mutated records bypass verification
ONLY in the test harness to exercise missing-evidence branches. Original records
must verify in both engines. No provider calls or recorded filesystem paths.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
DESKTOP = ROOT / 'desktop/ReservoirScope'
SOURCE = ROOT / 'native/ReservoirScope/Sources/ReservoirScope/GuidedLessons.swift'
EXAMPLES = ROOT / 'essentials/examples'
SWIFT_HARNESS = '''import Foundation
import EssentialsCore
struct Request: Decodable { let name: String; let record: ActionComparisonRecord?; let cursors: [Int]; let verify: Bool }
struct Evidence: Encodable { let state: String; let observation: String; let evidenceSteps: [Int] }
struct Row: Encodable { let name: String; let cursor: Int; let evidence: Evidence }
@main struct Oracle {
    static func main() throws {
        let requests = try JSONDecoder().decode([Request].self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var rows: [Row] = []
        for request in requests {
            if request.verify, let record = request.record { _ = try record.verify() }
            for cursor in request.cursors {
                let value = GuidedEvidenceEvaluator.evaluate(request.record, cursorStep: cursor)
                rows.append(Row(name: request.name, cursor: cursor, evidence: Evidence(state: value.state.rawValue, observation: value.observation, evidenceSteps: value.evidenceSteps)))
            }
        }
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        print(String(decoding: try encoder.encode(rows), as: UTF8.self))
    }
}
'''

def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_names():
    return (['essentials-actions-feedback.json']
        + [f'portable/example-component-{i}.json' for i in range(1, 9)]
        + [f'portable/example-model-{i}.json' for i in range(4, 9)]
        + [f'portable/{name}.json' for name in ['example-observation-scripted', 'example-observation-active-scripted', 'example-model-observation', 'example-model-observation-active']]
        + [f'portable/example-preparation-{i}.json' for i in range(1, 5)])


def mutation_specs():
    # Mutants are evaluator inputs, never verification successes or accepted files.
    def spec(name, stage, change, cursors):
        filename = f'portable/example-component-{stage}.json' if isinstance(stage, int) else f'portable/{stage}.json'
        return name, filename, change, cursors
    return [
        spec('empty-right-prefix', 1, lambda r: r['right'].update(frames=[]), [0, 1, 120]),
        spec('recurrence-missing-left', 2, lambda r: r.update(left=None), [1, 2, 30]),
        spec('recurrence-misaligned-prefix', 2, lambda r: r['left']['frames'].pop(0), [1, 2, 30]),
        spec('recurrence-identical-states', 2, lambda r: r['right'].update(frames=r['left']['frames']), [1, 2, 30]),
        spec('sensory-missing-measurement', 3, lambda r: r['right']['frames'][29].update(spectral=None), [29, 30]),
        spec('sensory-single-arm', 3, lambda r: r.update(left=None), [30]),
        spec('sensory-state-differs', 3, lambda r: r['right']['frames'][0]['state'].__setitem__(0, 0.8), [1, 30]),
        spec('journal-save-failed', 4, lambda r: r['right']['actions'][0]['saveReceipt'].update(status='failed'), [29, 30]),
        spec('journal-save-missing', 4, lambda r: r['right']['actions'][0].update(saveReceipt=None), [30]),
        spec('journal-cancelled', 4, lambda r: r['right']['actions'][0].update(status='cancelled'), [30]),
        spec('journal-single-arm', 4, lambda r: r.update(left=None), [30]),
        spec('return-application-future', 5, lambda r: r['right']['actions'][0].update(applicationStep=600), [29, 30, 31]),
        spec('return-application-absent', 5, lambda r: r['right']['actions'][0].update(applicationStep=None), [30, 31]),
        spec('return-frame-link-absent', 5, lambda r: r['right']['frames'][30].update(semanticActionID=None), [30, 31]),
        spec('return-vector-absent', 5, lambda r: r['right']['actions'][0].update(semanticVector=None), [30, 31]),
        spec('return-single-arm', 5, lambda r: r.update(left=None), [30, 31]),
        spec('memory-text-altered', 6, lambda r: r['right']['actions'][1].update(memoryText='altered memory'), [59, 60]),
        spec('memory-id-missing', 6, lambda r: r['right']['actions'][1].update(memoryEntryID='missing'), [59, 60]),
        spec('memory-prompt-excludes-text', 6, lambda r: r['right']['actions'][1].update(prompt='No earlier journal here.'), [60]),
        spec('memory-not-earlier', 6, lambda r: r['right']['journals'][0].update(observedStep=60), [59, 60]),
        spec('memory-journal-in-future', 6, lambda r: r['right']['journals'][0].update(observedStep=61), [60]),
        spec('memory-model-prepared', 'example-model-6', lambda r: r['right']['actions'][1].update(requestStarted=False), [60]),
        spec('memory-last-opportunity-failed', 6, lambda r: r['right']['actions'][0].update(status='failed'), [30]),
        spec('wait-failed', 7, lambda r: r['right']['actions'][2].update(status='failed'), [89, 90]),
        spec('wait-has-journal', 7, lambda r: r['right']['actions'][2].update(journalEntryID='unexpected'), [90]),
        spec('wait-has-save', 7, lambda r: r['right']['actions'][2].update(saveReceipt=r['right']['actions'][0]['saveReceipt']), [90]),
        spec('regulation-fill-missing', 8, lambda r: r['right']['frames'][119].update(fillPercent=None), [119, 120]),
        spec('regulation-retention-missing', 8, lambda r: r['right']['frames'][119].update(retentionUsed=None), [120]),
        spec('regulation-control-missing', 8, lambda r: r['right']['frames'][119].update(control=None), [120]),
        spec('regulation-lower-bound', 8, lambda r: r['right']['frames'][119]['control'].update(appliedRetention=0.82), [120]),
        spec('regulation-away-from-bound', 8, lambda r: r['right']['frames'][119]['control'].update(appliedRetention=0.95), [120]),
        spec('observation-missing-arm', 'example-observation-active-scripted', lambda r: r.update(left=None), [29, 30]),
        spec('observation-left-cancelled', 'example-observation-active-scripted', lambda r: r['left']['actions'][0].update(status='cancelled'), [29, 30]),
        spec('observation-right-failed', 'example-observation-active-scripted', lambda r: r['right']['actions'][0].update(status='failed'), [30]),
        spec('observation-no-left-opportunity', 'example-observation-active-scripted', lambda r: r['left'].update(actions=[]), [30]),
    ]


def inputs():
    yield {'name': 'unopened', 'record': None, 'cursors': [0, 1, 600], 'verify': False}, None
    for name in canonical_names():
        data = (EXAMPLES / name).read_bytes()
        record = json.loads(data)
        end = max((f['step'] for f in record['right']['frames']), default=0)
        yield {'name': name, 'record': record, 'cursors': list(range(end + 2)), 'verify': True}, sha(data)
    for name, filename, change, cursors in mutation_specs():
        data = (EXAMPLES / filename).read_bytes()
        record = json.loads(data)
        change(record)
        yield {'name': name, 'record': record, 'cursors': cursors, 'verify': False}, sha(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New receipt path; existing files are never overwritten')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; choose a fresh receipt path')
    environment = dict(os.environ, LC_ALL='C', LANG='C')
    subprocess.run(['cargo', 'build', '--locked', '-p', 'reservoir-core', '--example', 'guided_evidence_oracle'], cwd=DESKTOP, env=environment, check=True)
    core_sources = sorted(p for component in ['reservoir', 'spectral_bridge', 'llm', 'regulation', 'stages', 'actions'] for p in (ROOT / 'essentials' / component).glob('*.swift'))
    with tempfile.TemporaryDirectory(prefix='reservoir-guided-conformance-') as temporary:
        work = Path(temporary)
        subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '5', '-O', '-module-name', 'EssentialsCore', '-emit-library', '-static', '-emit-module', '-emit-module-path', str(work / 'EssentialsCore.swiftmodule'), *map(str, core_sources), '-framework', 'Accelerate', '-o', str(work / 'libEssentialsCore.a')], env=environment, check=True)
        harness = work / 'oracle.swift'
        harness.write_text(SWIFT_HARNESS)
        swift_binary = work / 'guided-swift'
        subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '6', '-O', '-I', str(work), '-L', str(work), '-lEssentialsCore', '-framework', 'Accelerate', str(SOURCE), str(harness), '-o', str(swift_binary)], env=environment, check=True)
        rust_binary = DESKTOP / 'target/debug/examples/guided_evidence_oracle'
        checks = []
        for request, source_hash in inputs():
            data = json.dumps([request], ensure_ascii=False, separators=(',', ':')).encode()
            path = work / 'input.json'
            path.write_bytes(data)
            swift = subprocess.run([str(swift_binary), str(path)], env=environment, capture_output=True, text=True)
            rust = subprocess.run([str(rust_binary), str(path)], env=environment, capture_output=True, text=True)
            row = {'name': request['name'], 'inputSha256': sha(data), 'canonicalSourceSha256': source_hash, 'verificationRequired': request['verify'], 'cursors': request['cursors'], 'swiftExit': swift.returncode, 'rustExit': rust.returncode}
            if swift.returncode == 0 and rust.returncode == 0:
                expected, actual = json.loads(swift.stdout), json.loads(rust.stdout)
                row['matched'] = expected == actual
                if not row['matched']:
                    row['differences'] = [{'swift': a, 'rust': b} for a, b in zip(expected, actual) if a != b][:10]
            else:
                row.update(matched=False, swiftError=swift.stderr[:2000], rustError=rust.stderr[:2000])
            checks.append(row)
            print(json.dumps({'name': request['name'], 'cursors': len(request['cursors']), 'matched': row['matched']}), flush=True)
        receipt = {'schema': 'reservoir-scope.guided-conformance.v1', 'executedAtUtc': datetime.now(timezone.utc).isoformat(), 'nativeSource': str(SOURCE.relative_to(ROOT)), 'nativeSourceSha256': sha(SOURCE.read_bytes()), 'swiftCoreSources': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p.read_bytes())} for p in core_sources], 'harnessSha256': sha(SWIFT_HARNESS.encode()), 'rustSourceSha256': sha((DESKTOP / 'crates/reservoir-core/src/guided_evidence.rs').read_bytes()), 'scriptSha256': sha(Path(__file__).read_bytes()), 'swiftVersion': subprocess.check_output(['xcrun', 'swift', '--version'], env=environment, text=True).strip(), 'modelsContacted': False, 'recordedPathsAccessed': False, 'checks': checks, 'caseCount': len(checks), 'cursorCount': sum(len(c['cursors']) for c in checks), 'passed': all(c['matched'] for c in checks), 'limits': 'Exact finite evaluator comparison, not full desktop parity or provider/storage authentication. Deliberate mutants bypass verification only in the harness. The accepted action verifier retains its existing ASCII and format scope. No 600-step regulation-window evaluator is tested here.'}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as output:
            json.dump(receipt, output, indent=2)
            output.write('\n')
        print(json.dumps({key: receipt[key] for key in ['passed', 'caseCount', 'cursorCount']}))
        if not receipt['passed']:
            raise SystemExit(1)

if __name__ == '__main__':
    main()
