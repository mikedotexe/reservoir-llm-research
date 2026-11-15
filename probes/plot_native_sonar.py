#!/usr/bin/env python3
"""Plot all six prospectively selected final-state native scans, without model calls.

These are descriptive endpoint measurements, not matched treatment effects.
Requires NumPy and Matplotlib; never writes the input reports.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    labels = [f'{cohort}-{model}' for cohort in ['independent', 'paused'] for model in ['gemma', 'glm', 'mistral']]
    reports = [json.loads((args.reports / f'{label}-scan.json').read_text()) for label in labels]
    assert all(r['status'] == 'scanned' and r['modelsContacted'] is False for r in reports)
    args.output.mkdir(parents=True, exist_ok=False)
    scans = [r['scan'] for r in reports]
    names = ['Gemma4', 'GLM-4.7-Flash', 'Ministral 3'] * 2
    matrices = [np.array(s['immediateResponseMatrix']) for s in scans]
    extent = max(float(abs(m).max()) for m in matrices)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    metadata = {'scope': 'Six final saved states; controls, held input, phase and prior history differ. No matched model comparison or global topology claim.', 'scans': []}
    for label, report in zip(labels, reports):
        scan = report['scan']
        metadata['scans'].append({'label': label, 'scanId': scan['id'], 'source': report['source'],
            'reportSha256': hashlib.sha256((args.reports / f'{label}-scan.json').read_bytes()).hexdigest(),
            'step': scan['origin']['step'], 'controls': scan['origin']['controls'],
            'leadingGains': [row[0] for row in scan['singularValues']],
            'directions': [{'direction': c['direction'], 'positiveFirstL2': c['positiveResponseL2'][0],
                'negativeFirstL2': c['negativeResponseL2'][0], 'positiveReturnStep': c['positiveReturnStep'],
                'negativeReturnStep': c['negativeReturnStep']} for c in scan['candidates']]})
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for i, (ax, matrix, scan, name) in enumerate(zip(axes.flat, matrices, scans, names)):
        image = ax.imshow(matrix, cmap='RdBu_r', vmin=-extent, vmax=extent, aspect='auto', interpolation='nearest')
        c = scan['origin']['controls']
        ax.set_title(f"{name} · {'independent' if i < 3 else 'paused peer-enabled'}\nstep {scan['origin']['step']} · leak {c['leak']:g} · gain {c['recurrentGain']:g}")
        ax.set_xlabel('Authored input coordinate (0–47)')
        if i % 3 == 0: ax.set_ylabel('Recurrent coordinate (0–31)')
    fig.suptitle('Native response maps at six saved endpoints', fontsize=16)
    fig.subplots_adjust(left=.07, right=.87, top=.85, bottom=.13, hspace=.52, wspace=.26)
    fig.colorbar(image, cax=fig.add_axes([.9, .25, .016, .48])).set_label('Signed central response per unit input')
    fig.text(.5, .035, '±0.01 coordinate probes on copies · shared color scale · channel indices are not spatial regions\nDifferent source conditions; these are local response maps, not a matched model comparison.', ha='center')
    fig.savefig(args.output / 'native-response-maps.png', dpi=180)
    fig.savefig(args.output / 'native-response-maps.pdf')
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharex=True, sharey=True)
    colors = {'strongest': '#197d78', 'weakest': '#c57725', 'persistent': '#8053ad'}
    for i, (ax, scan, name) in enumerate(zip(axes.flat, scans, names)):
        for candidate in scan['candidates']:
            for sign, style in [('positive', '-'), ('negative', '--')]:
                curve = np.maximum(1e-12, np.array(candidate[f'{sign}ResponseL2']))
                ax.plot(np.arange(1, 65), curve, style, color=colors[candidate['direction']], lw=1.5, label=candidate['direction'] if sign == 'positive' else None)
        ax.set_yscale('log'); ax.set_ylim(1e-12, 1); ax.grid(alpha=.18)
        ax.set_title(f"{name} · {'independent' if i < 3 else 'paused peer-enabled'}\nsource step {scan['origin']['step']}")
        ax.set_xlabel('Numerical steps after one input impulse')
        if i % 3 == 0: ax.set_ylabel('Recurrent L2 separation from baseline')
        ax.legend(fontsize=8, loc='upper right')
    fig.suptitle('How the copied input response fades', fontsize=16)
    fig.subplots_adjust(left=.08, right=.98, top=.85, bottom=.15, hspace=.52, wspace=.18)
    fig.text(.5, .035, 'Solid + / dashed − · equal input norm 0.01 · values below 10⁻¹² drawn at the floor\nHeld text and controls fixed; future writing/actions and sensory evolution are not simulated.', ha='center')
    fig.savefig(args.output / 'native-response-decay.png', dpi=180)
    fig.savefig(args.output / 'native-response-decay.pdf')
    plt.close(fig)
    metadata.update(numpyVersion=np.__version__, matplotlibVersion=matplotlib.__version__, sharedMatrixColorExtent=extent)
    (args.output / 'figure-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    main()
