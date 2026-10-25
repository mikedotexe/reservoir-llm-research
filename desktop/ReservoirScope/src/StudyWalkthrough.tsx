import { useState } from 'react';
import { conditionLabels, isSavedStudy, matchesReport, recalculate, reported, scoreRow, type Replay, type Rule, type SavedStudy } from './studyReplay';
import './studyWalkthrough.css';

// Private study text is explicitly staged for a local build. A source checkout
// without that packet still opens the reported finding and says what is missing.
const packets = import.meta.glob<string>('./local-studies/s021.json', { eager: true, query: '?raw', import: 'default' });
function readPacket(): unknown {
  const text = packets['./local-studies/s021.json'];
  if (!text) return null;
  try { return JSON.parse(text); } catch { return {invalid: true}; }
}
const savedStudy = readPacket();
const number = (value: number) => value.toLocaleString('en-US', {maximumFractionDigits:2});

function ResultsTable({result, rule}: {result: Replay; rule: Rule}) {
  return <div className="study-table-wrap" role="region" aria-label={`${rule === 'changed' ? 'Changed' : 'Unchanged'} rule results`} tabIndex={0}>
    <table>
      <caption>{rule === 'changed' ? 'Rule changed' : 'Rule stayed the same'} · 12 calls per row</caption>
      <thead><tr><th scope="col">Comparison before the choice</th><th scope="col">Correct direct</th><th scope="col">Wrong direct</th><th scope="col">Measure</th><th scope="col">Mean cost</th></tr></thead>
      <tbody>{result.groups.filter(g => g.rule === rule).map(g => <tr key={g.condition}>
        <th scope="row">{conditionLabels[g.condition]}</th><td>{g.correct}</td><td>{g.wrong}</td><td>{g.measure}</td><td>{number(g.cost/g.n)}</td>
      </tr>)}</tbody>
    </table>
  </div>;
}

function Example({study}: {study: SavedStudy}) {
  try {
    const pair = (['correct','flipped'] as const).map(condition => {
      const row = study.rows.find(r => r.base === 0 && r.rule === 'changed' && r.condition === condition && r.seed === 7);
      if (!row) throw new Error('Example is missing.');
      return {row, ...scoreRow(study, row)};
    });
    return <>
      <div className="study-facts"><strong>Same facts in both calls</strong><p>Station Sable01 · value <b>24</b> · current threshold <b>19</b> (previously 50). The correct direct route is HIGH.</p>
        <blockquote>“Its x is fixed from that snapshot onward; this says nothing about earlier values.”</blockquote>
        <p>This sentence was in the supplied task. A further measurement was unnecessary.</p>
      </div>
      <div className="study-example-pair">{pair.map(({row, action, account, cost}) => <article key={row.id}>
        <p className="study-label">Researcher-supplied comparison</p>
        <h3>{row.condition === 'correct' ? '24 ≥ 19 · correct (GE)' : '24 < 19 · flipped (LT)'}</h3>
        <p className="study-label">Model-generated choice & account</p>
        <strong className="study-action">{action === 'MEASURE' ? 'Measure again' : 'Route HIGH'}</strong>
        <blockquote>{account}</blockquote>
        <p className="study-outcome"><span>Simulated outcome</span> Correct route · cost {cost}{cost === 1 ? ' for measurement' : ''}</p>
        <details><summary>Exact prefix and continuation</summary>
          <p>Supplied assistant prefix</p><pre tabIndex={0}>{row.prefix}</pre>
          <p>Generated continuation, unchanged</p><pre tabIndex={0}>{row.suffix}</pre>
          <p className="study-id">{row.id}</p>
        </details>
      </article>)}</div>
      <p className="study-example-reading"><strong>What to notice:</strong> the flipped response says 24 is greater than 19, but treats the snapshot as insufficient. Its arithmetic and its account of what the evidence supports come apart.</p>
      <p className="study-small">Illustrative pair: world 00, changed rule, seed 7. Both calls were in the study’s fixed reading sample. This pair illustrates the finding; the table above covers every routing call.</p>
      <details><summary>Read the full shared task</summary>{study.prompts['0-changed']?.map((message, i) => <div key={i}><p>{message.role === 'system' ? 'System instruction' : 'User task'}</p><pre tabIndex={0}>{message.content}</pre></div>)}</details>
    </>;
  } catch {
    return <p role="alert">The saved example could not be read. The reported finding remains above; recalculation will report any data error.</p>;
  }
}

export default function StudyWalkthrough({active, study: suppliedStudy = savedStudy}: {active: boolean; study?: unknown}) {
  const study = isSavedStudy(suppliedStudy) ? suppliedStudy : null;
  const invalidPacket = suppliedStudy != null && !study;
  const [replay, setReplay] = useState<Replay | null>(null);
  const [message, setMessage] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [failed, setFailed] = useState(false);
  const calculate = () => {
    setAttempt(n => n+1);
    try {
      if (!study) throw new Error('This build does not include the saved study packet.');
      const result = recalculate(study);
      setReplay(result); setFailed(!matchesReport(result));
      setMessage(matchesReport(result)
        ? '72 of 72 saved calls recalculated. All six rows and the 12-pair comparison match the study report.'
        : 'Recalculation differs from the study report. The tables now show the recalculated values; the reported finding needs review.');
    } catch (error) {
      setReplay(null); setFailed(true);
      setMessage(`Recalculation stopped: ${error instanceof Error ? error.message : 'Invalid saved data.'} No incomplete result is shown. The tables retain the reported values.`);
    }
  };
  const result = replay ?? reported;
  return <section className="study-walkthrough" hidden={!active} aria-labelledby="study-title">
    <header className="study-heading">
      <p className="study-kicker">S-021 · saved study · 25 October 2026</p>
      <h1 id="study-title">Does a supplied comparison<br className="study-wide-break"/> change the next decision?</h1>
      <p>We gave a local language model verified facts and a routing rule, then changed the comparison immediately before its choice.</p>
      <nav aria-label="Study walkthrough"><a href="#study-question">1 · Question</a><a href="#study-result">2 · Result</a><a href="#study-example">3 · One example</a><a href="#study-recalculate">4 · Recalculate</a></nav>
    </header>

    <section id="study-question" aria-labelledby="study-question-title">
      <p className="study-step">01 / Question</p><h2 id="study-question-title">What changes when the comparison is wrong?</h2>
      <p>The model routed a fictional ticket LOW or HIGH by comparing a value with a threshold. We supplied either a correct or flipped comparison, or let the model generate one. Only <code>LT</code> versus <code>GE</code> changed between the correct and flipped inputs.</p>
      <p className="study-small">Same facts, task, model settings and paired seeds. Six authored worlds × two rule settings × three conditions × two seeds = <strong>72 saved calls</strong>. The baseline also changes how much text the model generates.</p>
    </section>

    <section id="study-result" aria-labelledby="study-result-title">
      <p className="study-step">02 / Result</p><h2 id="study-result-title">A flipped comparison prompted extra measurement</h2>
      <p>The study report found that, with the rule changed, correct comparisons led to 8 correct direct routes. Flipped comparisons led to 10 measurements and 2 wrong direct routes.</p>
      <div className="study-result-label">{replay ? 'Recalculated from saved outputs' : 'Reported results'}{replay && failed ? ' · differs from report' : ''}</div>
      <ResultsTable result={result} rule="changed" />
      <p className="study-cost-key">Cost: correct direct route <b>0</b> · wrong direct route <b>4</b> · measurement with automatic correct routing <b>1</b>. Lower is better.</p>
      <div className="study-finding"><strong>{number(result.pairedGain)} lower mean cost</strong><p>Correct versus flipped comparison, across 12 paired calls in the changed-rule condition (six worlds, two seeds). The report’s exact difference is 7/6.</p></div>
      <details><summary>Control: when the rule stayed the same</summary><ResultsTable result={result} rule="unchanged" /></details>
      <p className="study-limit">This supports sensitivity to researcher-supplied comparison text in this task. Benefit over letting the model generate the comparison remains uncertain. It does not establish private introspection or a benefit to Astrid or Minime.</p>
    </section>

    <section id="study-example" aria-labelledby="study-example-title">
      <p className="study-step">03 / One example</p><h2 id="study-example-title">Correct arithmetic, unnecessary measurement</h2>
      {study ? <Example study={study}/> : invalidPacket
        ? <p role="alert">The saved study packet is invalid. The exact example and recalculation are unavailable; the tables show the study’s reported results.</p>
        : <p>The private saved-output packet is not included in this build, so the exact example and recalculation are unavailable. The study’s reported results are shown above.</p>}
    </section>

    <section id="study-recalculate" aria-labelledby="study-recalculate-title">
      <p className="study-step">04 / Recalculate</p><h2 id="study-recalculate-title">Check the result from the saved outputs</h2>
      <p>Join each supplied prefix to its saved continuation, read the chosen action, and apply the routing costs. Rebuild all six table rows and the paired mean difference.</p>
      <p className="study-small">Runs locally and makes no model calls. This recalculates the displayed counts and costs; it does not rerun the experiment, bootstrap intervals, qualification checks or qualitative readings.</p>
      {study && <button className="primary-button" onClick={calculate}>Recalculate saved results <span aria-hidden="true">↻</span></button>}
      <div className={`study-replay-message${failed ? ' study-replay-error' : ''}`} role="status" aria-live="polite" aria-atomic="true">{message && <p key={attempt}>{message} <span className="study-small">Check {attempt}.</span></p>}</div>
      {replay && <p><strong>{number(replay.pairedGain)}</strong> mean cost difference · {replay.pairs} pairs · <a href="#study-result">See the recalculated table ↑</a></p>}
      <details className="study-provenance"><summary>Methods, source & reproduction details</summary>
        <p>One local model: Mistral Small 24B. Six authored worlds are the units for uncertainty; the 72 calls are not 72 independent worlds. The report gives a descriptive world-bootstrap interval of [1/3, 7/3] for the primary difference. It is not recomputed here.</p>
        <p>The source packet contains the original prefixes and generated continuations, shared prompts and world facts. Staging checks their hashes against the saved report. The app rejects missing, duplicate or malformed trials before showing a recalculation.</p>
        <p>Full account: <code>analyses/2026-10-25-prefix-continuation.md</code><br/>Protocol: <code>research/studies/S-021-prefix-continuation.md</code><br/>Build instructions: <code>desktop/ReservoirScope/S021-WALKTHROUGH.md</code></p>
        {study && <dl><dt>Model</dt><dd>{study.source.model} · Ollama {study.source.providerVersion}</dd><dt>Settings</dt><dd>Temperature {study.source.temperature} · context {study.source.contextTokens} · seeds 7 and 20260909</dd><dt>Model digest</dt><dd><code>{study.source.modelDigest}</code></dd><dt>Score SHA-256</dt><dd><code>{study.source.scoreSha256}</code></dd><dt>Design SHA-256</dt><dd><code>{study.source.designSha256}</code></dd><dt>Archive closure</dt><dd><code>{study.source.closedSha256}</code></dd></dl>}
      </details>
    </section>
  </section>;
}
