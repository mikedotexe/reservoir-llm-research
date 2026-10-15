#!/usr/bin/env python3
"""One explicitly authorized passive admission; never start a service or retry."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess

POLICY = {'requiredPressureLevel': 1, 'minimumFreePercent': 30,
          'minimumFreeDiskBytes': 8 * 1024**3, 'attempts': 1}
COMMANDS = (['/usr/sbin/sysctl', '-n', 'hw.memsize'],
            ['/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level'],
            ['/usr/bin/memory_pressure'])


def decision(results, disk, policy):
    if policy != POLICY:
        raise ValueError('Admission policy differs from the approved frozen 30% rule')
    total = pressure = free = None
    if len(results) == 3:
        for index in (0, 1):
            raw = results[index].get('stdout', '').strip()
            if results[index].get('exit') == 0 and re.fullmatch(r'\d+', raw):
                if index == 0:
                    total = int(raw)
                else:
                    pressure = int(raw)
        if results[2].get('exit') == 0:
            matches = re.findall(r'System-wide memory free percentage:\s*(\d+)%', results[2].get('stdout', ''))
            if len(matches) == 1 and 0 <= int(matches[0]) <= 100:
                free = int(matches[0])
    admitted = (len(results) == 3 and all(x.get('exit') == 0 for x in results)
                and total is not None and total > 0 and pressure == policy['requiredPressureLevel']
                and free is not None and free >= policy['minimumFreePercent']
                and type(disk) is int and disk >= policy['minimumFreeDiskBytes'])
    return dict(totalMemoryBytes=total, pressureLevel=pressure, freePercent=free,
                diskFreeBytes=disk, admitted=admitted)


def main(root=None):
    root = Path(__file__).resolve().parent if root is None else Path(root)
    # Exclusivity precedes every probe; a partial receipt also forbids a rerun.
    with (root / 'host-admission-01.json').open('x') as stream:
        raw = (root / 'evaluation-freeze-01.json').read_bytes()
        frozen = json.loads(raw)
        plan_path = root / 'run-plan.json'
        plan_raw = plan_path.read_bytes()
        plan_identity = dict(path=str(plan_path.resolve()), bytes=len(plan_raw), sha256=hashlib.sha256(plan_raw).hexdigest())
        if plan_identity not in frozen['files']:
            raise ValueError('Run plan is not bound by the prospective freeze')
        for item in frozen['files']:
            data = Path(item['path']).read_bytes()
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError(f"Frozen file changed: {item['path']}")
        plan = json.loads(plan_raw)
        policy = plan['provenance']['hostAdmission']
        if plan['episodeId'] != 'context-sources-03' or policy != POLICY:
            raise ValueError('Wrong episode or admission policy')
        results = []
        for command in COMMANDS:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                results.append(dict(command=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append(dict(command=command, error=str(error)))
        values = decision(results, shutil.disk_usage(root).free, policy)
        receipt = dict(capturedUtc=dt.datetime.now(dt.timezone.utc).isoformat(), episodeId=plan['episodeId'],
                       scope='One passive pre-launch admission. No service/Being inspection or process changes. No retry.',
                       freezeSha256=hashlib.sha256(raw).hexdigest(), runPlan=plan_identity,
                       policyId=plan['provenance']['admissionPolicyId'], thresholds=policy,
                       results=results, **values)
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
        stream.flush()
    print(json.dumps(values))


if __name__ == '__main__':
    main()
