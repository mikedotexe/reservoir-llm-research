#!/usr/bin/env python3
"""Offline, outcome-independent first external/fresh audio neighborhood for S-003.

Reads retained JSON only; writes research outputs. Standard-library calculations;
matplotlib is used only to render figures. No live access or causal estimation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT / 'research/outputs/2026-09-07-first-audio')
    args = ap.parse_args()
    args.output = args.output.resolve()
    output_root = (ROOT / 'research/outputs').resolve()
    if not args.output.is_relative_to(output_root) or args.output == output_root:
        ap.error('Choose a new output directory beneath research/outputs.')
    if args.output.exists() and any(args.output.iterdir()):
        ap.error('Output directory is not empty; preserve evidence by choosing a new path.')
    paths = {
        'bridge': ROOT / 'research/outputs/2026-09-06-input-fill/bridge.json',
        'native': ROOT / 'research/outputs/2026-09-06-around-0919/source/episode-evidence.json',
        'viewer': ROOT / 'visualizations/reservoir-3d/data.json',
    }
    data = {k: json.loads(p.read_text()) for k, p in paths.items()}
    rows = data['bridge']['tables']['bridge_messages']['rows']
    packets = [dict(r, decoded=json.loads(r['payload'])) for r in rows
               if r['topic'] == 'consciousness.v1.telemetry']
    audio = sorted([r for r in packets if r['decoded']['modalities']['audio_source'] == 'external'
                    and r['decoded']['modalities']['audio_freshness_class'] == 'fresh_sample'],
                   key=lambda r: (r['timestamp'], r['id']))
    assert audio[0]['id'] == 13958590, 'Previously declared first event has changed.'
    native = [r for r in data['native']['records'] if r['kind'] == 'telemetry'
              and r['source']['locator'].get('table') == 'eigenvalue_timeline']
    esn = {(r['payload']['session_id'], r['payload']['timestamp']): r
           for r in data['native']['records'] if r['kind'] == 'telemetry'
           and r['source']['locator'].get('table') == 'esn_metrics'}
    native.sort(key=lambda r: (r['payload']['session_id'], r['payload']['timestamp']))
    sessions = {r['payload']['session_id'] for r in native}
    assert sessions == {5316}, sessions
    start = native[0]['source']['locator']['session']['start_time']
    t0 = audio[0]['decoded']['t_ms'] / 1000
    records = []
    for i, r in enumerate(native):
        p = r['payload']; e = esn[(p['session_id'], p['timestamp'])]
        prev = native[i-1]['payload'] if i else None
        records.append(dict(native_id=r['source_record_id'], esn_id=e['source_record_id'],
            native_payload_sha256=r['source']['sha256'], esn_payload_sha256=e['source']['sha256'],
            session_id=p['session_id'], native_session_s=p['timestamp'],
            native_derived_epoch=r['occurred_at'], seconds_from_packet_t_ms=p['timestamp']-t0,
            fill_pct=100*p['fill_ratio'],
            fill_slope_pp_per_s=100*(p['fill_ratio']-prev['fill_ratio'])/(p['timestamp']-prev['timestamp']) if prev else None,
            cascade_cov_lambda1=p['lambda1'], esn_cov_lambda1=e['payload']['esn_eig1'],
            geom_rel=e['payload']['esn_geom_rel'], esn_leak=e['payload']['esn_leak']))
    viewer = {tuple(r['source_ids']): r for r in data['viewer']['samples']}
    for r in records:
        v = viewer[(int(r['native_id'].split(':')[1]), int(r['esn_id'].split(':')[1]))]
        assert abs(v['fill_pct']-r['fill_pct']) < 1e-7
        if r['fill_slope_pp_per_s'] is not None:
            assert abs(v['fill_rate_pct_per_s']-r['fill_slope_pp_per_s']) < 1e-6

    def neighbors(anchor):
        nearest_i = min(range(len(records)), key=lambda i: abs(records[i]['native_session_s']-anchor))
        def item(r):
            return dict(r, seconds_from_anchor=r['native_session_s']-anchor)
        return {
            'strictly_prior': item([r for r in records if r['native_session_s'] < anchor][-1]),
            'nearest': item(records[nearest_i]),
            'strictly_following': item([r for r in records if r['native_session_s'] > anchor][0]),
            'prior_to_nearest': item(records[nearest_i-1]),
            'following_nearest': item(records[nearest_i+1]),
        }

    event_details = []
    for r in audio:
        p = r['decoded']; s = p['t_ms']/1000
        ns = neighbors(s); nr = ns['nearest']
        event_details.append(dict(bridge_row_id=r['id'], bridge_log_epoch=r['timestamp'],
            packet_t_ms=p['t_ms'], packet_t_ms_plus_session_start_epoch=start+s,
            log_minus_session_derived_s=r['timestamp']-(start+s),
            seconds_from_first_packet_t_ms=s-t0,
            payload_sha256=hashlib.sha256(r['payload'].encode()).hexdigest(),
            modalities=p['modalities'], semantic_energy_v1=p['semantic_energy_v1'],
            bridge_fill_pct=100*p['fill_ratio'], bridge_fill_column_pct=r['fill_pct'],
            bridge_esn_leak=p['esn_leak'],
            source_clock_neighbors=ns, wall_clock_neighbors=neighbors(r['timestamp']-start),
            nearest_fill_discrepancy_pp=100*p['fill_ratio']-nr['fill_pct'],
            nearest_leak_discrepancy=p['esn_leak']-nr['esn_leak']))
    differences = [r['timestamp']-(start+r['decoded']['t_ms']/1000) for r in packets]
    sends = [r for r in rows if r['topic'] == 'consciousness.v1.sensory']
    if not sends:
        raise ValueError('Expected semantic send topic missing; inspect schema.')
    scopes = {}
    for name, low, high in [('backdrop', -90, 90), ('detail', -15, 30), ('preceding', -90, 0)]:
        nr = [r for r in records if low <= r['seconds_from_packet_t_ms'] <= high]
        br = [r for r in packets if low <= r['decoded']['t_ms']/1000-t0 <= high]
        sr = [r for r in sends if low <= r['timestamp']-start-t0 <= high]
        if name == 'preceding':
            # Packet construction follows the matching recorded state by milliseconds.
            # Exclude that candidate same-loop record from the preceding trajectory.
            nr = [r for r in nr if r['native_session_s'] < event_details[0]['source_clock_neighbors']['nearest']['native_session_s']]
            br = [r for r in br if r['decoded']['t_ms']/1000 < t0]
        scopes[name] = dict(requested_source_relative_bounds_s=[low, high], n_native_pairs=len(nr),
            native_selection_note='For preceding only, exclude nearest matching record; earlier trajectory is not a no-input control.',
            n_bridge_telemetry_source_clock=len(br), n_semantic_sends_bridge_log_clock=len(sr),
            semantic_bridge_row_ids=[r['id'] for r in sr],
            native_ids=[r['native_id'] for r in nr],
            native_sample_span_s=nr[-1]['native_session_s']-nr[0]['native_session_s'],
            observed_ranges={k:[min(r[k] for r in nr), max(r[k] for r in nr)]
                for k in ['fill_pct', 'fill_slope_pp_per_s', 'esn_cov_lambda1', 'geom_rel', 'esn_leak']})
    args.output.mkdir(parents=True, exist_ok=True)
    context = [r for r in records if -90 <= r['seconds_from_packet_t_ms'] <= 90]
    with (args.output/'native-neighborhood.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(context[0])); writer.writeheader(); writer.writerows(context)
    retained_bridge = [r for r in rows if -94 <= r['timestamp']-start-t0 <= 94]
    (args.output/'bridge-neighborhood.json').write_text(json.dumps(retained_bridge, indent=2)+'\n')
    summary = dict(schema_version=1, kind='first_external_audio_neighborhood',
        selection='First chronological external + fresh_sample audio telemetry report of two in the saved 20-minute interval; fixed before neighborhood metrics were inspected.',
        scope='Exploratory reuse; one selected report, overlapping other inputs, no effect estimate.',
        input_files={k:dict(path=str(p.relative_to(ROOT)), sha256=digest(p)) for k,p in paths.items()},
        probe_sha256=digest(Path(__file__)), native_session_id=5316, session_start_epoch=start,
        capture_queries={'bridge':{k:v for k,v in data['bridge']['tables']['bridge_messages'].items() if k!='rows'},
            'native':[c for c in data['native']['coverage'] if c.get('table') in ['eigenvalue_timeline','esn_metrics']]},
        full_capture_counts=dict(native_pairs=len(records), bridge_telemetry=len(packets),
            external_fresh_audio_reports=len(audio), semantic_sends=len(sends)),
        clock_status='Packet t_ms and native timestamps are compared under shared-session elapsed-clock assumption. Matching fill and leak support record proximity; no exact consumption link. Bridge log clock is separately preserved, without an offset correction.',
        log_minus_session_derived_seconds=dict(n=len(differences), minimum=min(differences),
            median=statistics.median(differences), maximum=max(differences)),
        viewer_validation='All 507 source-ID pairs and rounded fill/slope values checked against viewer; calculations use original native precision.',
        definitions=dict(fill_pct='100 * eigenvalue_timeline.fill_ratio; estimator level',
            fill_slope_pp_per_s='Backward native fill difference divided by exact session elapsed seconds',
            geom_rel='Native esn_metrics.esn_geom_rel; radius relative to its baseline',
            esn_cov_lambda1='Native reservoir-state covariance eigenvalue; distinct from cascade',
            esn_leak='Recorded get_leak value, not reconstructed effective per-step coefficient'),
        neighborhoods=scopes, audio_reports=event_details,
        limitations=['External audio means a routed audio-feature envelope; origin is unknown and may include host synthesis. It does not establish microphone or environmental sound.',
            'No exact sensor-capture, arrival, consumed sample or admission tick identified.',
            'Packet audio_age_ms belongs to modality observation; not subtracted as an authenticated capture clock.',
            'No historical per-step controller action/mode or binary identity established.',
            'Semantic send marks retain bridge log clock and denote co-occurrence, not silent controls.',
            'The interval between clock markers is a discrepancy guide, not a confidence interval or proven capture-time bound.'])

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    for name, limits in [('backdrop',(-90,90)), ('detail',(-15,30))]:
        fig, axs = plt.subplots(4,1,figsize=(12,9),sharex=True)
        fig.subplots_adjust(top=.82,bottom=.11,left=.10,right=.90,hspace=.24)
        ts=[r['seconds_from_packet_t_ms'] for r in context]
        for ax, key, label, color in zip(axs,
                ['fill_pct','fill_slope_pp_per_s','geom_rel','esn_cov_lambda1'],
                ['Fill (%)','Fill change\n(pp / second)','Native geometry\n(radius / baseline)','Native covariance λ₁'],
                ['#087b9b','#087b9b','#693b99','#1b7951']):
            ax.plot(ts,[r[key] for r in context],'.-',color=color,ms=4,lw=1.1)
            ax.set_ylabel(label,color=color); ax.grid(alpha=.17)
            ax.set_xlim(*limits)
            for event in event_details:
                xp=event['seconds_from_first_packet_t_ms']; xl=xp+event['log_minus_session_derived_s']
                if limits[0]<=xp<=limits[1]:
                    ax.axvline(xp,color='#20252b',lw=1.1)
                    ax.axvline(xl,color='#c17013',ls='--',lw=1.1)
                    ax.axvspan(min(xp,xl),max(xp,xl),color='#c17013',alpha=.08)
        axs[1].axhline(0,color='#777',lw=.7)
        axs[2].axhline(1,color='#777',lw=.7)
        ax2=axs[3].twinx(); ax2.spines['right'].set_visible(True)
        ax2.plot(ts,[r['esn_leak'] for r in context],color='#a03a58',lw=1,alpha=.8)
        ax2.set_ylabel('Recorded leak',color='#a03a58')
        sx=[r['timestamp']-start-t0 for r in sends]
        axs[0].plot(sx,[.035]*len(sx),'|',transform=axs[0].get_xaxis_transform(),color='#9678ba',ms=9)
        axs[0].text(.01,.06,'Semantic sends (bridge log clock)',transform=axs[0].transAxes,
                    color='#775099',fontsize=8)
        for i,event in enumerate(event_details):
            xp=event['seconds_from_first_packet_t_ms']
            if limits[0]<=xp<=limits[1]:
                axs[0].text(xp+.6,.94,f'Audio report {i+1}',transform=axs[0].get_xaxis_transform(),fontsize=9,va='top')
        axs[-1].set_xlabel('Seconds from first packet t_ms = 505335.534 s (conditional shared-session axis)')
        fig.suptitle('First fresh audio-feature report: an existing fill rise, with a geometry excursion',
                     x=.10,y=.98,ha='left',fontsize=15)
        fig.text(.10,.942,'September 6, 2026 · bridge log 09:13:49.045 Pacific · source marked external; audio origin unknown',fontsize=10)
        fig.legend(handles=[Line2D([0],[0],color='#20252b',label='Packet elapsed clock'),
            Line2D([0],[0],color='#c17013',ls='--',label='Same report: bridge log clock'),
            Line2D([0],[0],marker='|',ls='',color='#9678ba',label='Semantic send: bridge log clock')],
            loc='upper left',bbox_to_anchor=(.095,.922),ncol=3,frameon=False,fontsize=9)
        fig.text(.10,.035,'Clock markers differ by 3.604 s for report 1 (1.255 s for report 2). Shading is a discrepancy guide, not a timing bound.\n'
                 'Native dots are saved records; connecting lines guide reading. No exact audio-consumption step or causal response is established.',fontsize=9)
        fig.savefig(args.output/f'{name}.png',dpi=150); plt.close(fig)
    summary['output_sha256']={p.name:digest(p) for p in args.output.iterdir() if p.name in
        ['native-neighborhood.csv','bridge-neighborhood.json','backdrop.png','detail.png']}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'output':str(args.output), 'neighborhoods':scopes,
                      'first_source_clock_neighbors':event_details[0]['source_clock_neighbors']},indent=2))


if __name__ == '__main__':
    main()
