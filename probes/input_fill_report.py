#!/usr/bin/env python3
"""Describe a bounded input/fill capture without accessing the live systems.

Analysis uses only the standard library. Matplotlib is required solely to export
the scientific overview figures. All paths default to saved research evidence;
outputs must remain inside this repository and existing outputs are never replaced.
No response attribution, significance test, periodicity estimate, interpolation,
or reconstruction of historical controller state is performed.
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
LOCAL = ZoneInfo('America/Los_Angeles')
DEFAULT_OUTPUT = REPO / 'research/outputs/2026-09-06-input-fill'
MAX_INPUT = 64 * 1024 * 1024
OUTPUT_NAMES = ('summary.json', 'event-brackets.csv', 'overview.png', 'input-context.png')


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Expected a finite numeric value: {value!r}')
    return float(value)


def read_json(path):
    path = path.resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError(f'Input exceeds the bounded read limit: {path}')
    return json.loads(raw), {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec='microseconds')


def describe(values):
    numbers = [finite(value) for value in values if value is not None]
    return {'n': len(numbers), 'min': min(numbers), 'max': max(numbers),
            'mean': statistics.mean(numbers), 'median': statistics.median(numbers)} if numbers else {'n': 0}


def frequencies(values):
    return dict(sorted(Counter('unknown' if v is None else str(v).lower() if isinstance(v, bool) else str(v)
                               for v in values).items()))


def load_evidence(telemetry_path, bridge_path):
    telemetry, telemetry_source = read_json(telemetry_path)
    bridge, bridge_source = read_json(bridge_path)
    samples = telemetry['samples']
    if len(samples) < 2:
        raise ValueError('At least two recorded samples are required')
    times = [datetime.fromisoformat(s['t_utc'].replace('Z', '+00:00')).timestamp() for s in samples]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Telemetry wall times must be strictly increasing')
    if len({s['session_id'] for s in samples}) != 1:
        raise ValueError('This bounded report requires one engine session')
    if any(len(s['source_ids']) != 2 or None in s['source_ids'] for s in samples):
        raise ValueError('Telemetry must retain its exact paired source IDs')
    table = bridge['tables']['bridge_messages']
    if table['truncated'] or table['n'] != len(table['rows']):
        raise ValueError('Bridge capture is incomplete or its count disagrees')
    rows = sorted(table['rows'], key=lambda r: (r['timestamp'], r['id']))
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate bridge record IDs')
    parsed = [(r, json.loads(r['payload']) if isinstance(r['payload'], str) else r['payload']) for r in rows]
    return telemetry, bridge, samples, times, parsed, {'telemetry': telemetry_source, 'bridge': bridge_source}


def analyze(telemetry, bridge, samples, times, parsed, sources):
    slopes = [None]
    for previous, current in zip(samples, samples[1:]):
        elapsed = finite(current['t_s']) - finite(previous['t_s'])
        if elapsed <= 0:
            raise ValueError('Recorded elapsed times must increase')
        slopes.append((finite(current['fill_pct']) - finite(previous['fill_pct'])) / elapsed)
    supplied_slopes = [abs(a - b['fill_rate_pct_per_s']) for a, b in zip(slopes[1:], samples[1:])]
    if max(supplied_slopes) > 1e-6:
        raise ValueError('Recomputed slopes disagree with the saved derivative')
    events, contexts = [], []
    for row, payload in parsed:
        if row['topic'] == 'consciousness.v1.sensory':
            delivery = payload.get('delivery_v1', {})
            sent_ms = delivery.get('sent_at_unix_ms')
            event_time = finite(sent_ms) / 1000 if sent_ms is not None else finite(row['timestamp'])
            before = bisect.bisect_left(times, event_time) - 1
            after = bisect.bisect_right(times, event_time)
            before_valid, after_valid = before >= 0, after < len(times)
            features = payload.get('features')
            if features is not None:
                features = [finite(value) for value in features]
            event = {
                'bridge_row_id': row['id'], 'delivery_id': delivery.get('delivery_id'),
                'payload_sha256': delivery.get('payload_sha256'),
                'kind': payload.get('kind'), 'direction': row['direction'],
                'event_stage': 'recorded outgoing attempt; receipt/admission not established by this report',
                'event_timestamp_basis': 'delivery_v1.sent_at_unix_ms' if sent_ms is not None else 'bridge_messages.timestamp fallback',
                'sent_at_unix_ms': sent_ms, 'event_time_utc': utc(event_time),
                'bridge_log_time_utc': utc(row['timestamp']),
                'log_minus_event_s': row['timestamp'] - event_time,
                'attempted_feature_dimensions': len(features) if features is not None else None,
                'attempted_vector_l2_norm': math.sqrt(sum(v * v for v in features)) if features is not None else None,
                'effective_admitted_vector_l2_norm': None,
                'before_sample_index': before if before_valid else None,
                'after_sample_index': after if after_valid else None,
                'before_time_utc': samples[before]['t_utc'] if before_valid else None,
                'after_time_utc': samples[after]['t_utc'] if after_valid else None,
                'before_cascade_row_id': samples[before]['source_ids'][0] if before_valid else None,
                'before_esn_row_id': samples[before]['source_ids'][1] if before_valid else None,
                'after_cascade_row_id': samples[after]['source_ids'][0] if after_valid else None,
                'after_esn_row_id': samples[after]['source_ids'][1] if after_valid else None,
                'since_before_s': event_time - times[before] if before_valid else None,
                'until_after_s': times[after] - event_time if after_valid else None,
                'before_fill_pct': samples[before]['fill_pct'] if before_valid else None,
                'after_fill_pct': samples[after]['fill_pct'] if after_valid else None,
                'bracket_fill_change_pp': samples[after]['fill_pct'] - samples[before]['fill_pct'] if before_valid and after_valid else None,
                'boundary_exclusion': 'none' if before_valid and after_valid else 'missing_before' if not before_valid else 'missing_after',
                'within_1ms_of_recorded_telemetry_time': any(abs(t - event_time) <= 0.001001 for t in times[max(0, before):min(len(times), after + 1)]),
                '_epoch': event_time,
            }
            events.append(event)
        elif row['topic'] == 'consciousness.v1.telemetry':
            contexts.append({'bridge_row_id': row['id'], 'bridge_log_epoch': row['timestamp'],
                'bridge_log_time_utc': utc(row['timestamp']), 'source_engine_t_ms': payload.get('t_ms'),
                'modalities': payload.get('modalities', {}), 'semantic_energy_v1': payload.get('semantic_energy_v1', {})})
    events.sort(key=lambda e: (e['_epoch'], e['bridge_row_id']))
    intervals = []
    event_times = [event['_epoch'] for event in events]
    for i in range(1, len(samples)):
        included = events[bisect.bisect_right(event_times, times[i - 1]):bisect.bisect_right(event_times, times[i])]
        intervals.append({'before_sample_index': i - 1, 'after_sample_index': i,
            'before_time_utc': samples[i - 1]['t_utc'], 'after_time_utc': samples[i]['t_utc'],
            'before_source_ids': samples[i - 1]['source_ids'], 'after_source_ids': samples[i]['source_ids'],
            'elapsed_s': samples[i]['t_s'] - samples[i - 1]['t_s'],
            'fill_change_pp': samples[i]['fill_pct'] - samples[i - 1]['fill_pct'],
            'fill_slope_pp_per_s': slopes[i], 'outgoing_attempt_count': len(included),
            'bridge_row_ids': [e['bridge_row_id'] for e in included]})
    for event in events:
        a, b = event['before_sample_index'], event['after_sample_index']
        event['outgoing_attempts_in_strict_bracket'] = (
            bisect.bisect_left(event_times, times[b]) - bisect.bisect_right(event_times, times[a])
            if a is not None and b is not None else None)
    metrics = {key: describe(s.get(key) for s in samples) for key in
               ('fill_pct', 'esn_leak', 'esn_cov_lambda1', 'geom_radius', 'geom_rel')}
    metrics['fill_slope_pp_per_s'] = describe(slopes)
    modality_fields = sorted({key for item in contexts for key in item['modalities']})
    semantic_fields = sorted({key for item in contexts for key in item['semantic_energy_v1']})
    modality_counts = {key: frequencies(item['modalities'].get(key) for item in contexts)
                       for key in modality_fields if key.endswith(('_source', '_class', '_fired'))}
    modality_numbers = {key: describe(item['modalities'].get(key) for item in contexts)
                        for key in modality_fields if key.endswith(('_age_ms', '_rms', '_var'))}
    semantic_counts = {key: frequencies(item['semantic_energy_v1'].get(key) for item in contexts)
                       for key in semantic_fields if key in ('admission', 'input_active', 'kernel_active')}
    semantic_numbers = {key: describe(item['semantic_energy_v1'].get(key) for item in contexts)
                        for key in semantic_fields if key.endswith(('_energy', '_delta', '_ms'))}
    summary = {
        'schema_version': 1, 'kind': 'input_fill_descriptive_report',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'protocol': 'research/studies/S-003-input-and-fill.md',
        'sources': sources,
        'selection': {'since_utc': utc(bridge['since']), 'until_utc_exclusive': utc(bridge['until']),
            'timezone': 'America/Los_Angeles', 'reason': 'Reuse of the prior clock-selected window; exploratory, not independent confirmation'},
        'denominators': {'saved_telemetry_pairs': len(samples), 'telemetry_intervals': len(intervals),
            'all_bridge_rows': len(parsed), 'bridge_telemetry_rows': len(contexts), 'outgoing_attempts': len(events),
            'fully_bracketed_outgoing_attempts': sum(e['boundary_exclusion'] == 'none' for e in events),
            'boundary_exclusions': frequencies(e['boundary_exclusion'] for e in events),
            'timestamp_near_boundary_1ms': sum(e['within_1ms_of_recorded_telemetry_time'] for e in events),
            'intervals_with_outgoing_attempts': sum(i['outgoing_attempt_count'] > 0 for i in intervals),
            'intervals_without_recorded_outgoing_attempts': sum(i['outgoing_attempt_count'] == 0 for i in intervals),
            'intervals_with_multiple_outgoing_attempts': sum(i['outgoing_attempt_count'] > 1 for i in intervals),
            'bracketed_events_sharing_strict_bracket_with_another': sum((e['outgoing_attempts_in_strict_bracket'] or 0) > 1 for e in events),
            'codec_impact_rows': bridge['tables'].get('codec_impact', {}).get('n')},
        'bridge_topic_counts': frequencies(r['topic'] for r, p in parsed),
        'attempt_kind_counts': frequencies(e['kind'] for e in events),
        'attempt_timestamp_basis_counts': frequencies(e['event_timestamp_basis'] for e in events),
        'attempt_log_minus_event_s': describe(e['log_minus_event_s'] for e in events),
        'attempted_vector_l2_norm': describe(e['attempted_vector_l2_norm'] for e in events),
        'attempt_interarrival_s': describe(b - a for a, b in zip(event_times, event_times[1:])),
        'telemetry_interval_s': describe(i['elapsed_s'] for i in intervals),
        'metric_summaries': metrics,
        'modality_counts': modality_counts, 'modality_numeric_summaries': modality_numbers,
        'semantic_counts': semantic_counts, 'semantic_numeric_summaries': semantic_numbers,
        'external_audio_reports': [c for c in contexts if c['modalities'].get('audio_source') == 'external'],
        'validation': {'max_difference_from_saved_fill_slope_pp_per_s': max(supplied_slopes),
            'source_id_order': ['eigenvalue_timeline.id', 'esn_metrics.id']},
        'definitions': {
            'fill_pct': telemetry['definitions']['fill_pct'],
            'fill_slope_pp_per_s': 'Backward difference of adjacent saved fill percentages divided by their high-precision recorded t_s difference; not the engine smoothed derivative.',
            'event_bracket': 'Last strictly earlier and first strictly later saved telemetry UTC values. CSV includes both source IDs and offsets. No interpolated response or state-update linkage.',
            'interval_assignment': 'Outgoing attempt timestamps in (previous telemetry UTC, current telemetry UTC]. An event exactly equal to a telemetry time is excluded from strict event brackets at that endpoint, but remains assigned once in this interval table.',
            'attempt_magnitude': 'Euclidean norm of the transmitted features only; effective admitted magnitude is unknown here.',
            'bridge_context_clock': 'Modalities and semantic telemetry plotted at bridge_messages.timestamp (table log time). Retained payload t_ms is an engine-relative source timestamp; it is not joined to individual native ESN updates.',
            'event_clock_precision': 'Sent timestamps are integer Unix milliseconds. Saved telemetry UTC strings are serialized to milliseconds. Event brackets compare those recorded values; <=1ms proximity is flagged. t_s preserves more precise elapsed intervals.',
        },
        'limitations': [
            'Close telemetry ticks and overlapping events are dependent; no causal effect, significance or periodicity claim is estimated.',
            'No recorded outgoing attempt in an interval does not establish absence of other inputs or internal stimulation.',
            'This report does not join delivery receipts. An outgoing attempt is not evidence of receipt, admission or successful state update.',
            'Semantic admission telemetry describes the recorded state of a channel, not proof that a specific outgoing attempt was admitted.',
            'Audio/video source and freshness labels are retained as reported; they do not establish external sensory content or a device state.',
            'Historical controller stage, PI state and applied actuator sequence are not reconstructed from fill. The later health snapshot is excluded.',
            'Native ESN leak is a mixing coefficient, not a fill drain. ESN covariance and sensory-field spectral quantities remain distinct.',
        ],
        'telemetry_interval_mapping': intervals,
        'bridge_context_mapping': contexts,
    }
    return summary, events, contexts, slopes


def attach_deliveries(path, summary, events):
    if path is None:
        return
    capture, source = read_json(path)
    if capture['bridge_capture_sha256'] != summary['sources']['bridge']['sha256']:
        raise ValueError('Delivery capture refers to a different bridge capture')
    receipts = {}
    for row in capture['records']:
        if hashlib.sha256(row['raw_line_utf8'].encode()).hexdigest() != row['raw_line_sha256']:
            raise ValueError('Delivery raw-line hash mismatch')
        payload = row['payload']
        if json.loads(row['raw_line_utf8']) != payload:
            raise ValueError('Delivery payload differs from raw line')
        if payload.get('event') == 'receipt_verified':
            if payload['delivery_id'] in receipts:
                raise ValueError('Multiple verified receipts for one delivery ID')
            receipts[payload['delivery_id']] = row
    for event in events:
        row = receipts.get(event['delivery_id'])
        payload = row['payload'] if row else {}
        if row and (payload['payload_sha256'] != event['payload_sha256'] or event['bridge_row_id'] not in row['bridge_row_ids']):
            raise ValueError('Receipt identity or payload hash differs from bridge send')
        event.update({'receipt_event': payload.get('event'), 'receipt_status': payload.get('status'),
            'receipt_id': payload.get('receipt_id'), 'receipt_source_row_id': row['row_id'] if row else None,
            'receipt_raw_line_sha256': row['raw_line_sha256'] if row else None,
            'received_at_unix_ms': payload.get('received_at_unix_ms'),
            'routed_at_unix_ms': payload.get('routed_at_unix_ms'),
            'receipt_recorded_at_unix_ms': payload.get('recorded_at_unix_ms'),
            'receipt_spectral_causation_established': payload.get('spectral_causation_established')})
        if payload.get('status') == 'accepted':
            event['event_stage'] = 'acknowledged semantic send; accepted receipt, no exact state-update linkage'
    summary['sources']['deliveries'] = source
    summary['denominators']['accepted_verified_receipts'] = sum(e['receipt_status'] == 'accepted' for e in events)
    summary['receipt_status_counts'] = frequencies(e['receipt_status'] for e in events)
    summary['receipt_spectral_causation_established_counts'] = frequencies(e['receipt_spectral_causation_established'] for e in events)
    summary['limitations'][2] = 'Verified receipts establish acknowledged transport with the recorded status. They do not establish an exact successful state update or spectral effect; receipt clocks are kept separate from send clocks.'
    summary['definitions']['receipt_join'] = 'Exact delivery_id, payload_sha256 and bridge row identity; raw receipt line hashes verified. Event alignment remains at the sender timestamp, not receiver or receipt-log time.'


def plot_outputs(output, samples, times, events, contexts, slopes, summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.labelcolor': '#24364b', 'text.color': '#24364b',
        'axes.titleweight': 'bold', 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    color = {'fill': '#177d91', 'slope': '#ab6437', 'leak': '#734bad', 'lambda': '#377bbc',
             'geometry': '#447e55', 'attempt': '#ac4652'}
    x = [datetime.fromtimestamp(t, LOCAL) for t in times]
    event_x = [datetime.fromtimestamp(e['_epoch'], LOCAL) for e in events]
    begin = datetime.fromisoformat(summary['selection']['since_utc']).astimezone(LOCAL)
    end = datetime.fromisoformat(summary['selection']['until_utc_exclusive']).astimezone(LOCAL)
    fig, axes = plt.subplots(6, 1, figsize=(16, 12), sharex=True,
        gridspec_kw={'height_ratios': [2.1, 1.4, 1.3, 1.3, 1.3, 0.7]})
    fig.subplots_adjust(top=.90, bottom=.18, left=.10, right=.965, hspace=.25)
    acknowledged = summary['denominators'].get('accepted_verified_receipts', 0)
    send_label = 'acknowledged semantic sends' if acknowledged == len(events) else 'recorded outgoing attempts'
    fig.suptitle('Recorded input and reservoir movement', x=.10, ha='left', y=.97, fontsize=21)
    fig.text(.10, .935, f'September 6, 2026 · 09:09–09:29 Pacific · {len(samples)} paired state observations · {len(events)} {send_label}', fontsize=11)
    channels = [('fill_pct', 'Fill (%)', color['fill']), (None, 'Fill slope\n(pp/s)', color['slope']),
                ('esn_leak', 'ESN leak\n(coefficient)', color['leak']),
                ('esn_cov_lambda1', 'ESN state\ncovariance λ₁', color['lambda']),
                ('geom_radius', 'ESN geometry\n(RMS norm)', color['geometry'])]
    for ax, (key, label, line_color) in zip(axes, channels):
        values = slopes if key is None else [s[key] for s in samples]
        ax.plot(x, values, color=line_color, linewidth=.95)
        ax.set_ylabel(label, labelpad=13)
        ax.grid(axis='y', color='#dce3e9', linewidth=.65)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    axes[1].axhline(0, color='#8995a2', linewidth=.8, zorder=0)
    axes[5].eventplot(event_x, lineoffsets=.5, linelengths=.7, linewidths=.85, colors=color['attempt'])
    axes[5].set_ylim(0, 1)
    axes[5].set_yticks([])
    axes[5].set_ylabel('Acknowledged\nsends' if acknowledged == len(events) else 'Outgoing\nattempts', labelpad=18)
    axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=2, tz=LOCAL))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=LOCAL))
    axes[-1].set_xlim(begin, end)
    axes[-1].set_xlabel('Recorded time · America/Los_Angeles')
    fig.text(.10, .045, 'Send markers use sender time, not receipt time; state traces use saved telemetry time. Lines connect recorded samples.\n'
        'Accepted receipts acknowledge transport. Temporal neighbors do not establish a successful state update or an input effect.\n'
        'Fill is an estimator percentage; slope is a backward difference. Leak and native ESN covariance are separate quantities.',
        fontsize=10, va='bottom', linespacing=1.55, color='#516274')
    with (output / 'overview.png').open('xb') as stream:
        fig.savefig(stream, format='png', dpi=170)
    plt.close(fig)

    if not contexts:
        raise ValueError('No bridge telemetry context available for the second figure')
    cx = [datetime.fromtimestamp(c['bridge_log_epoch'], LOCAL) for c in contexts]
    fig, axes = plt.subplots(4, 1, figsize=(16, 10), sharex=True,
        gridspec_kw={'height_ratios': [1.25, 1.7, 1.6, .9]})
    fig.subplots_adjust(top=.83, bottom=.15, left=.13, right=.965, hspace=.27)
    fig.suptitle('What the bridge telemetry recorded about input', x=.13, ha='left', y=.97, fontsize=21)
    fig.text(.13, .915, f'{len(contexts)} bridge telemetry rows · shown at table log time\nSource engine t_ms is retained in summary.json; no exact state-update join is asserted.', fontsize=11, linespacing=1.6, va='top')
    binary = [('modalities', 'audio_fired', 'Audio fired'), ('modalities', 'video_fired', 'Video fired'),
        ('modalities', 'history_fired', 'History fired'), ('semantic_energy_v1', 'input_active', 'Semantic active'),
        ('semantic_energy_v1', 'kernel_active', 'Kernel active')]
    for index, (section, field, label) in enumerate(binary):
        yes = [time for time, context in zip(cx, contexts) if context[section].get(field) is True]
        no = [time for time, context in zip(cx, contexts) if context[section].get(field) is False]
        unknown = [time for time, context in zip(cx, contexts) if context[section].get(field) is None]
        axes[0].scatter(no, [index]*len(no), s=5, color='#dbe0e5')
        axes[0].scatter(yes, [index]*len(yes), s=8, color='#177d91')
        axes[0].scatter(unknown, [index]*len(unknown), s=10, marker='x', color='#ac4652')
    axes[0].set_yticks(range(len(binary)), [item[2] for item in binary])
    axes[0].invert_yaxis()
    axes[0].set_title('Reported activity flags · teal = true; pale gray = false; red × = unavailable', loc='left', fontsize=10)
    energy_colors = ['#177d91', '#734bad', '#ab6437', '#377bbc']
    for field, line_color in zip(['input_energy', 'kernel_energy', 'regulator_drive_energy', 'kernel_delta'], energy_colors):
        axes[1].plot(cx, [c['semantic_energy_v1'].get(field) for c in contexts], label=field, color=line_color, linewidth=.9)
    axes[1].set_yscale('symlog', linthresh=1e-7)
    axes[1].set_ylabel('Recorded semantic values\n(symlog scale)')
    axes[1].legend(loc='upper right', frameon=True, fontsize=8, ncols=2)
    for field, line_color in [('audio_age_ms', '#377bbc'), ('video_age_ms', '#ab6437')]:
        axes[2].plot(cx, [c['modalities'].get(field, math.nan) / 1000 for c in contexts], label=field.replace('_age_ms', ''), color=line_color, linewidth=.9)
    axes[2].set_yscale('log')
    axes[2].set_ylabel('Reported source age\n(seconds; log scale)')
    axes[2].legend(loc='upper right', frameon=True, fontsize=9)
    admissions = sorted({str(c['semantic_energy_v1'].get('admission', 'unknown')) for c in contexts})
    for i, admission in enumerate(admissions):
        points = [time for time, c in zip(cx, contexts) if str(c['semantic_energy_v1'].get('admission', 'unknown')) == admission]
        axes[3].scatter(points, [i]*len(points), s=8, color='#734bad')
    labels = [v.replace('stable_core_', 'stable_core_\n') for v in admissions]
    axes[3].set_yticks(range(len(admissions)), labels, fontsize=8)
    axes[3].set_ylabel('Admission\nlabel', labelpad=14)
    for ax in axes:
        ax.grid(axis='y', color='#dce3e9', linewidth=.65)
    axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=2, tz=LOCAL))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=LOCAL))
    axes[-1].set_xlim(begin, end)
    axes[-1].set_xlabel('Bridge table log time · America/Los_Angeles')
    external_times = ', '.join(datetime.fromtimestamp(c['bridge_log_epoch'], LOCAL).strftime('%H:%M:%S.%f')[:-3] for c in summary['external_audio_reports'])
    fig.text(.13, .035, f'External/fresh audio was reported at {external_times} Pacific (table log times).\n'
        'Reported semantic kernel energy is a derived channel value, not a measured state-update effect or native ESN activation norm.\n'
        'Channel labels do not identify sensory content or the admission of a particular send. Full counts and source IDs are retained in summary.json.',
        fontsize=10, va='bottom', linespacing=1.6, color='#516274')
    with (output / 'input-context.png').open('xb') as stream:
        fig.savefig(stream, format='png', dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--telemetry', type=Path, default=REPO / 'visualizations/reservoir-3d/data.json')
    parser.add_argument('--bridge', type=Path, default=DEFAULT_OUTPUT / 'bridge.json')
    parser.add_argument('--deliveries', type=Path, default=DEFAULT_OUTPUT / 'deliveries.json')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(REPO):
        raise ValueError('Outputs must remain inside this research repository')
    if any((output / name).exists() for name in OUTPUT_NAMES):
        raise FileExistsError('Refusing to overwrite any report output; choose a new output directory')
    output.mkdir(parents=True, exist_ok=True)
    telemetry, bridge, samples, times, parsed, sources = load_evidence(args.telemetry, args.bridge)
    summary, events, contexts, slopes = analyze(telemetry, bridge, samples, times, parsed, sources)
    attach_deliveries(args.deliveries, summary, events)
    summary['sources']['probe'] = {'path': str(Path(__file__).resolve()),
        'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    plot_outputs(output, samples, times, events, contexts, slopes, summary)
    if not events:
        raise ValueError('No outgoing events available for the requested event-bracket report')
    columns = [key for key in events[0] if not key.startswith('_')]
    with (output / 'event-brackets.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(events)
    summary['outputs'] = {name: {'path': str(output / name), 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest()}
                          for name in OUTPUT_NAMES if name != 'summary.json'}
    with (output / 'summary.json').open('x') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: summary[key] for key in ('denominators', 'metric_summaries', 'modality_counts',
        'semantic_counts', 'attempt_interarrival_s', 'attempt_log_minus_event_s', 'validation')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
