import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { api, errorText } from './api';
import { acceptedLessonReplacement, comparisonAtCursor, continueTarget, GUIDE_RESUME_KEY, readGuideResume, rms, sourceForLesson, stateDifference, type GuideComparison, type GuideSource } from './guideNavigation';
import RecordedExperiments from './RecordedExperiments';
import { MechanicalEvidence } from './RecordEvidence';
import { RecordingController } from './recordingController';
import type { GuideCatalog, GuideLesson } from './types';
import './guide.css';

export default function GuidedTour({ active, onOpenExample }: { active: boolean; onOpenExample: (id: string) => void }) {
  const [controller] = useState(() => new RecordingController(api));
  const reading = useSyncExternalStore(controller.subscribe, controller.snapshot);
  const [resume] = useState(() => { try { return readGuideResume(window.localStorage); } catch { return { stage: 1, row: 0, source: 'scripted' as GuideSource }; } });
  const [catalog, setCatalog] = useState<GuideCatalog | null>(null);
  const [stage, setStage] = useState(resume.stage);
  const [source, setSource] = useState<GuideSource>(resume.source);
  const [catalogError, setCatalogError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [playbackOpen, setPlaybackOpen] = useState(false);
  const [comparison, setComparison] = useState<GuideComparison | null>(null);
  const started = useRef(false);
  const generation = useRef(0);
  const lesson = catalog?.lessons.find(item => item.stage === stage);
  const expectedSource = lesson ? sourceForLesson(lesson, source) : null;
  const matches = Boolean(expectedSource && reading.record?.filename === expectedSource.file);
  const track = reading.record?.tracks.find(item => item.id === reading.trackId);
  const target = lesson && track && reading.frame && matches ? continueTarget(lesson, track, reading.frame.step) : null;

  useEffect(() => {
    let current = true;
    api.guideCatalog().then(result => { if (current) setCatalog(result); }).catch(error => { if (current) setCatalogError(errorText(error)); });
    return () => { current = false; };
  }, []);
  useEffect(() => () => { generation.current++; void controller.close(); }, [controller]);
  useEffect(() => { if (!active) { controller.pause(); setPlaybackOpen(false); } }, [active, controller]);

  async function openLesson(next: GuideLesson, preference: GuideSource, row = 0) {
    const request = ++generation.current;
    const example = sourceForLesson(next, preference);
    const previousId = controller.snapshot().record?.recordId;
    controller.pause(); setPlaybackOpen(false); setLoading(true); setMessage('Opening and verifying the recorded lesson…');
    await controller.open(example.id);
    if (request !== generation.current) return;
    let current = controller.snapshot();
    if (!acceptedLessonReplacement(previousId, current.record, example.file) || current.opening) {
      setLoading(false); setMessage(current.message || 'The requested lesson was not opened. The previous reading remains available.'); return;
    }
    const right = current.record.tracks.find(item => item.id === 'right') ?? current.record.tracks.find(item => item.frameCount > 0);
    if (right) {
      await controller.selectTrack(right.id);
      if (request !== generation.current) return;
      if (row > 0 && right.frameCount > 0) await controller.seek(Math.min(row, right.frameCount - 1));
    }
    if (request !== generation.current) return;
    current = controller.snapshot();
    setStage(next.stage); setSource(preference); setLoading(false); setMessage(current.loadingFrame ? 'Reading the checkpoint…' : '');
  }

  useEffect(() => {
    if (!active || !catalog || started.current) return;
    started.current = true;
    const next = catalog.lessons.find(item => item.stage === resume.stage) ?? catalog.lessons[0];
    if (next) void openLesson(next, resume.source, resume.row);
  }, [active, catalog]);

  useEffect(() => {
    if (!matches || !reading.frame || loading) return;
    try { window.localStorage.setItem(GUIDE_RESUME_KEY, JSON.stringify({ stage, source, row: reading.frame.index })); } catch { /* Preference persistence is optional; records remain readable. */ }
  }, [stage, source, matches, loading, reading.frame]);

  useEffect(() => {
    if (!active || loading || !matches || !reading.record || !reading.frame || !reading.trackId) return;
    const record = reading.record, current = reading.frame;
    const cursor = { recordId: record.recordId, trackId: reading.trackId, step: current.step };
    const other = record.tracks.find(item => item.id !== reading.trackId && item.frameCount > 0);
    if (!other) { setComparison({ ...cursor, frame: null, message: 'This recording has one arm. No matched state comparison is available.' }); return; }
    const point = other.timeline.find(item => item.step === current.step);
    if (!point) { setComparison({ ...cursor, frame: null, message: 'No matching recorded step is available in the other track.' }); return; }
    let valid = true;
    const requestId = `guide-pair-${record.recordId}-${current.step}-${other.id}`;
    api.recordFrame(requestId, record.recordId, other.id, point.index).then(result => {
      if (!valid) return;
      if (result.requestId !== requestId || result.recordId !== record.recordId || result.trackId !== other.id || result.frame.step !== current.step) throw new Error('Matched-frame response does not belong to this cursor.');
      setComparison({ ...cursor, frame: result.frame, message: `Same recorded step · ${other.label} compared with ${track?.label ?? reading.trackId}` });
    }).catch(error => { if (valid) setComparison({ ...cursor, frame: null, message: errorText(error) }); });
    return () => { valid = false; };
  }, [active, loading, matches, reading.record, reading.frame, reading.trackId]);

  async function continueLesson() {
    controller.pause();
    if (!target || !catalog) return;
    if (target.kind === 'checkpoint') await controller.seek(target.index);
    else if (target.kind === 'lesson') { const next = catalog.lessons.find(item => item.stage === target.stage); if (next) await openLesson(next, source); }
  }
  if (!active) return null;
  if (!catalog) return <section className="notice" role={catalogError ? 'alert' : 'status'}><h2>Guided tour</h2><p>{catalogError || 'Loading and checking lessons…'}</p></section>;
  if (!lesson) return <p className="notice warning">The selected lesson is absent from the packaged catalog.</p>;

  const actualModel = source === 'recordedModel' && lesson.modelExample !== null;
  const paired = comparisonAtCursor(comparison, reading.record?.recordId, reading.trackId, reading.frame?.step);
  const difference = paired?.frame && reading.frame ? stateDifference(paired.frame.state, reading.frame.state) : null;
  return <section className="guided-tour" aria-labelledby="guide-heading">
    <div className="guide-header"><div><h1 id="guide-heading">Guided tour</h1><p>Explore eight recorded lessons, from input through writing, memory and choice. Opening a lesson starts no model or experiment.</p></div><label>Example source <select value={source} disabled={loading} onChange={event => void openLesson(lesson, event.target.value as GuideSource)}><option value="scripted">Scripted example</option><option value="recordedModel">Recorded model run</option></select></label></div>
    <nav className="guide-lessons" aria-label="Guided lessons">{catalog.lessons.map(item => <button key={item.stage} aria-current={item.stage === stage ? 'step' : undefined} disabled={loading} onClick={() => void openLesson(item, source)}><span>{String.fromCharCode(64 + item.stage)}</span><strong>{item.title}</strong></button>)}</nav>
    <section className="guide-lesson"><h2>{lesson.question}</h2><p className="guide-action">{lesson.suggestedAction}</p><details className="guide-interpretation"><summary>What to notice and what remains uncertain</summary><div className="guide-expectations"><div><h3>What to look for</h3><p>{actualModel ? lesson.modelExpected : lesson.expected}</p></div><div><h3>Interpretation limit</h3><p>{lesson.limitation}</p></div></div><p className="guide-provenance">{expectedSource?.provenance}</p></details>{matches && reading.frame && !loading && <MechanicalEvidence frame={reading.frame} />}{source === 'recordedModel' && !actualModel && <p className="guide-source-note">This lesson uses the numerical example. Your recorded-model preference is retained for D–H.</p>}</section>
    <div className="guide-progress"><div className="guide-checkpoints" aria-label="Authored checkpoints">{lesson.checkpoints.map(step => {
      const point = matches ? track?.timeline.find(item => item.step === String(step)) : null;
      const current = reading.frame?.step === String(step);
      return <button key={step} disabled={loading || reading.loadingFrame || !point} aria-current={current ? 'step' : undefined} onClick={() => { controller.pause(); if (point) void controller.seek(point.index); }}>Step {step}{!point && matches ? ' · unavailable' : ''}</button>;
    })}</div><div className="guide-progress-actions"><button aria-expanded={playbackOpen} aria-controls="guided-record-playback" disabled={loading || !matches} onClick={() => { if (playbackOpen) controller.pause(); setPlaybackOpen(!playbackOpen); }}>{playbackOpen ? 'Hide playback controls' : 'Show playback controls'}</button><button className="primary-button" disabled={loading || reading.loadingFrame || !target || target.kind === 'complete'} onClick={() => void continueLesson()}>{target?.kind === 'checkpoint' ? `Continue to step ${target.step}` : target?.kind === 'lesson' ? `Continue to lesson ${String.fromCharCode(64 + target.stage)}` : target?.kind === 'complete' ? 'Final checkpoint reached' : 'Continue'}</button></div></div>
    {(message || loading) && <p className="reader-message" role="status">{message}</p>}
    {!matches && !loading && <div className="notice"><p>The current reading is outside this lesson. Open the lesson to resume its checkpoints.</p><button onClick={() => void openLesson(lesson, source)}>Open lesson {String.fromCharCode(64 + lesson.stage)}</button></div>}
    <RecordedExperiments active={active && !loading} controller={controller} embedded hidePlayback={!playbackOpen} turnCursorStep={reading.frame?.step ?? '0'} />
    {matches && reading.frame && !loading && <section className="guide-measurements"><div><span className="eyebrow">CURRENT FRAME · STEP {reading.frame.step}</span><h3>Recorded measurements</h3><dl><dt>Input RMS</dt><dd>{rms(reading.frame.input)?.toPrecision(7) ?? 'Empty recorded vector'}</dd><dt>State RMS</dt><dd>{rms(reading.frame.state)?.toPrecision(7) ?? 'Empty recorded vector'}</dd><dt>State difference RMS</dt><dd>{difference === null ? 'No matched comparison' : difference.toPrecision(7)}</dd></dl></div><p>{paired?.message ?? 'Reading the matched frame…'}<br />RMS is calculated from the displayed recorded vectors. This same-step comparison does not identify the first divergence or evaluate memory benefit.</p></section>}
    <section className="guide-comparisons"><h3>Other recorded studies</h3><p>Observation channels and the 600-step sensory-field controller are separate studies. Their outcomes do not score writing quality or replace the A–H lesson.</p><div>{catalog.comparisons.map(example => <button key={example.id} onClick={() => onOpenExample(example.id)}><strong>{example.title}</strong><span>{example.provenance}</span></button>)}</div></section>
    <details className="guide-authorship"><summary>About these lessons and sources</summary><p>Questions, expected observations, suggested actions and interpretation limits come from the included native guide. Expected observations are teaching prompts; current measurements and verification results remain separate.</p><p>Continue moves to the next lesson checkpoint and pauses. Playback advances recorded frames; hiding its controls pauses it.</p><p className="hash">Lesson catalog SHA-256: {catalog.lessonsSha256}</p><p className="hash">Example catalog SHA-256: {catalog.examplesSha256}</p><p>{expectedSource?.file} · {expectedSource?.format}</p></details>
  </section>;
}
