"""Prepare finite, verified offline fixtures and an explicitly grouped catalog. No model calls."""
from pathlib import Path
import argparse, json, subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
names = ['Minimal reservoir', 'Recurrence', 'Sensory observer', 'Journal output', 'Reservoir return', 'Journal memory', 'Action choice', 'Regulation']
items = []

def prepare(name, spec, command='actions'):
    output = a.output / name
    recipe = a.output / (name.removeprefix('example-').removesuffix('.json') + '.recipe.json')
    if not output.exists():
        recipe.write_text(json.dumps(spec, indent=2) + '\n')
        subprocess.run([str(a.cli), command, '--config', str(recipe), '--output', str(output)], check=True)
    subprocess.run([str(a.cli), 'verify', str(output)], check=True)
    return json.loads(output.read_text())

def entry(identifier, title, file, record, provenance, group, order, lesson=None):
    items.append(dict(id=identifier, title=title, file=file, format=record['format'], provenance=provenance,
                      group=group, order=order, lessonID=lesson))

for stage in range(1, 9):
    name = f'example-component-{stage}.json'
    spec = dict(stage=stage, mode='fixedReplay', comparePrevious=stage > 1, steps=120, turnEvery=30, seed=20260909,
        question=f'What changes when adding {names[stage-1].lower()}?',
        expectedDifference='Inspect the named mechanism and its actual consequences.',
        alternativeExplanation='Repeated scripted writing tests mechanical transport, not adaptive interpretation.',
        stoppingPoint='120 steps; preserve all opportunities and stop on failure.')
    record = prepare(name, spec)
    entry(f'component-{stage}', f'{chr(64+stage)} · {names[stage-1]}', name, record,
          'Scripted example · 120 steps · exact mechanical comparison', 'guided', stage, chr(64+stage))

for active in [False, True]:
    name = 'example-observation-active-scripted.json' if active else 'example-observation-scripted.json'
    spec = dict(stage=4, mode='independentGeneration', comparePrevious=True, comparisonKind='observation',
        steps=120, turnEvery=30, seed=20260909,
        forcingProfile='continuousSensoryV1' if active else 'pulsedSensoryV1',
        question='What changes when measured reservoir coordinates are supplied?',
        expectedDifference='Only the designated prompt contains the current indexed reservoir state.',
        alternativeExplanation='Scripted responses qualify exposure and transport only.',
        stoppingPoint='120 steps, three paired opportunities; retain failures.')
    record = prepare(name, spec)
    if active:
        magnitudes = [max(map(abs, record['right']['frames'][step-1]['state'])) for step in [30, 60, 90]]
        if not all(x >= .25 for x in magnitudes): raise ValueError('Active-state fixture did not qualify: ' + str(magnitudes))
        (a.output / 'active-state-qualification.json').write_text(json.dumps(dict(
            schema='reservoir-scope.active-state-qualification.v1', steps=[30,60,90],
            minimum_maximum_absolute_state=.25, observed_maximum_absolute_state=magnitudes,
            scope='Qualified teaching fixture; no claim about writing quality.'), indent=2)+'\n')
    entry('observation-active-scripted' if active else 'observation-scripted',
          'What can the journal observe? · active input' if active else 'What can the journal observe? · quiet input',
          name, record, 'Scripted example · identical trajectory · two observation channels', 'comparison', 1 if active else 3)

name = 'example-regulation-controller.json'
record = prepare(name, {}, command='regulation')
entry('regulation-controller', 'Controller mechanism · reduced target error', name, record,
      'Scripted numerical example · sensory field and controller only · 600 steps', 'comparison', 5)

for path in sorted(a.output.glob('example-model-*.json')):
    subprocess.run([str(a.cli), 'verify', str(path)], check=True)
    record = json.loads(path.read_text()); spec = record['specification']; stage = spec['stage']
    observation = spec.get('comparisonKind') == 'observation'
    active = spec.get('forcingProfile') == 'continuousSensoryV1'
    title = ('What can the journal observe? · ' + ('active input' if active else 'quiet input')) if observation else f'{chr(64+stage)} · {names[stage-1]}'
    entry(path.stem, title, path.name, record,
          'Recorded model run · ' + spec['language']['model'] + ' · ' + record['status'] + ' · '
          + str(len(record['right']['frames'])) + ' of ' + str(spec['steps']) + ' steps',
          'comparison' if observation else 'model', (2 if active else 4) if observation else stage,
          None if observation else chr(64+stage))
for path in sorted(a.output.glob('example-preparation-*.json')):
    subprocess.run([str(a.cli), 'verify', str(path)], check=True)
    record = json.loads(path.read_text())
    entry(path.stem, 'Model preparation · attempt ' + path.stem.rsplit('-',1)[-1], path.name, record,
          'Recorded model run · qualification · ' + record['status'] + ' · ' + str(len(record['right']['frames'])) + ' steps',
          'preparation', int(path.stem.rsplit('-',1)[-1]))
(a.output / 'examples-index.json').write_text(json.dumps(items, indent=2)+'\n')
print('Catalog:', len(items), 'verified examples')
