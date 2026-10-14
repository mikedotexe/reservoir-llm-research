import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import JournalMeasurements from './JournalMeasurements';
import { MyReservoirJournalDetail } from './MyReservoirJournals';
import { formatRecordedMeasurement, readMeasurementReference } from './journalMeasurementReference';
import { DEFAULT_SUSTAINED_CONFIG, type JournalMeasurementReference } from './myReservoirTypes';
import { journal, reservoirFixture, settle } from './myReservoirTestFixtures';

function reference(step = 60): JournalMeasurementReference {
  return { currentStep: step, previousStep: step - 30, comparisonAvailable: true, rows: [
    { key: 'rms', label: 'Recurrent reservoir RMS', unit: 'dimensionless', current: .79182555, previous: .22602112, delta: .56580443 },
    { key: 'l2', label: 'Recurrent reservoir L2 norm', unit: 'dimensionless', current: 4.47, previous: 1.27, delta: 3.2 },
    { key: 'leadingSensoryEigenvalue', label: 'Largest sensory covariance eigenvalue', unit: 'dimensionless', current: 27.48050683, previous: .65409215, delta: 26.82641468 },
    { key: 'fillPercent', label: 'Reduced sensory active-mode fill', unit: 'percent', current: 15.18181927, previous: 94.31040364, delta: -79.12858437 },
    { key: 'headSharePercent', label: 'Top-eight sensory head share', unit: 'percent', current: 80, previous: 49, delta: 31 },
    { key: 'shoulderSharePercent', label: 'Top-eight sensory shoulder share', unit: 'percent', current: 12.4565, previous: 17.3262, delta: -4.8697 },
    { key: 'tailSharePercent', label: 'Top-eight sensory tail share', unit: 'percent', current: 7.5435, previous: 33.6738, delta: -26.1303 },
    { key: 'entropy', label: 'Top-eight sensory normalized entropy', unit: 'dimensionless', current: .44, previous: .81, delta: -.37 },
  ] };
}

describe('optional recorded measurements', () => {
  it('distinguishes the compact v5 prompt from full retained measurements without changing historical v4 presentation', () => {
    const entry = { ...journal(), observedStep: 60, text: 'An open entry with no required measurement claim.', measurementReference: reference() };
    const current = renderToStaticMarkup(<MyReservoirJournalDetail journal={entry} revision="8" config={DEFAULT_SUSTAINED_CONFIG}/>);
    const table = current.match(/<table[\s\S]*?<\/table>/)![0];
    expect(table.match(/scope="row"/g)).toHaveLength(8);
    expect(table).toContain('Largest sensory covariance eigenvalue');
    expect(current).toContain('prompt supplies only current and prior recurrent RMS and separate sensory fill with their differences, plus state-coordinate L2 distance');
    expect(current).toContain('it does not supply this full table');
    expect(current).toContain('values that were not supplied as part of that readout');
    expect(current).toContain('exact prompt records what was supplied, including prior prose');
    expect(current).toContain(entry.text); expect(current).not.toMatch(/<details[^>]*\bopen/);
    const historical = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...entry, promptVersion: 'reservoir-journal-v4' }} revision="8" config={DEFAULT_SUSTAINED_CONFIG}/>);
    expect(historical).not.toContain('v5 prompt');
    expect(historical).not.toContain('it does not supply this full table');
    expect(historical.match(/<table[\s\S]*?<\/table>/)![0]).toBe(table);
    expect(historical).toContain('reservoir-journal-v4');
  });
  it('keeps eight backend rows collapsed after original prose and before separate Evidence', () => {
    const text = 'My present RMS is 999. The shoulder is expanding.\n<script>inert writing</script>';
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), observedStep: 60, text, measurementReference: reference() }} revision="8"/>);
    const prose = html.indexOf('My present RMS is 999.'), measurements = html.indexOf('<summary>Recorded measurements</summary>'), evidence = html.indexOf('<summary>Evidence</summary>');
    expect(prose).toBeLessThan(measurements); expect(measurements).toBeLessThan(evidence);
    expect(html).not.toMatch(/<details[^>]*\bopen/);
    expect(html).toContain('&lt;script&gt;inert writing&lt;/script&gt;');
    const table = html.match(/<table[\s\S]*?<\/table>/)![0];
    expect(table.match(/scope="row"/g)).toHaveLength(8);
    expect(table).toContain('0.79182555'); expect(table).toContain('27.480507'); expect(table).toContain('-4.8697 pp');
    expect(table).not.toContain('999'); expect(table).not.toContain('expanding');
    expect(html).toContain('not spatial regions'); expect(html).toContain('does not assess or change the writing');
    expect(html).not.toContain('role="alert"'); expect(html).not.toContain('quality pass');
  });

  it('uses observation steps independently of remembered journal identity and live state', () => {
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(9), observedStep: 60, measurementReference: reference(), memory: { entryId: 'journal-at-step-10', text: 'Previously claimed RMS 888', sha256: 'a'.repeat(64) } }} revision="200"/>);
    const table = html.match(/<table[\s\S]*?<\/table>/)![0];
    expect(table).toContain('Current · step 60'); expect(table).toContain('Prior · step 30');
    expect(table).not.toContain('step 10'); expect(table).not.toContain('888');
    expect(html).toContain('separate from the prose and the current live state');
  });

  it('distinguishes a first observation from a historical prior whose scalar snapshot was not retained', () => {
    const missing = { ...reference(), comparisonAvailable: false, rows: reference().rows.map(row => ({ ...row, previous: null, delta: null })) };
    const first = renderToStaticMarkup(<JournalMeasurements value={{ ...missing, previousStep: null }} observedStep={60}/>);
    expect(first).toContain('No previous observation is recorded'); expect(first).toContain('Prior · unavailable');
    const historical = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), promptVersion: 'reservoir-journal-v3', observedStep: 60, measurementReference: missing }} revision="8"/>);
    expect(historical).toContain('previous observation was at step 30'); expect(historical).toContain('scalar measurements are not retained');
    expect(historical).not.toContain('No previous observation is recorded');
    expect(historical.match(/<td>Unavailable<\/td>/g)).toHaveLength(16);
  });

  it('renders an unavailable explanation for omitted references without extracting numbers from the retained observation or prose', () => {
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), text: 'RMS 123456', observation: { rms: .999 }, measurementReference: undefined }} revision="8"/>);
    expect(html).toContain('Structured measurements were not supplied'); expect(html).not.toContain('<table');
    expect(html).toContain('RMS 123456'); expect(html).toContain('&quot;rms&quot;: 0.999');
  });

  it('fails only the structured table for malformed or mismatched references, leaving exact writing and evidence available', () => {
    const good = reference();
    const bad = [
      { ...good, currentStep: 61 }, { ...good, previousStep: 60 }, { ...good, previousStep: null },
      { ...good, rows: good.rows.slice(1) }, { ...good, rows: [...good.rows, good.rows[0]] },
      { ...good, rows: good.rows.map((row, i) => i ? row : { ...row, current: Number.NaN }) },
      { ...good, rows: good.rows.map((row, i) => i ? row : { ...row, unit: 'percent' }) },
      { ...good, rows: good.rows.map((row, i) => i ? row : { ...row, previous: null }) },
      { ...good, comparisonAvailable: false },
    ];
    for (const value of bad) {
      expect(readMeasurementReference(value, 60).reference).toBeNull();
      const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), observedStep: 60, text: 'Keep the full entry', measurementReference: value as JournalMeasurementReference }} revision="8"/>);
      expect(html).not.toContain('<table'); expect(html).toContain('Keep the full entry'); expect(html).toContain('exact retained observation remains available in Evidence');
      expect(html).toContain('Exact prompt');
    }
  });

  it('formats only display precision, signs and percentage-point labels without turning tiny changes into zero', () => {
    expect(formatRecordedMeasurement(.00000000003456, true)).toBe('+3.456e-11');
    expect(formatRecordedMeasurement(-4.8697, true)).toBe('-4.8697');
    expect(formatRecordedMeasurement(0, true)).toBe('0');
    const html = renderToStaticMarkup(<JournalMeasurements value={reference()} observedStep={60}/>);
    expect(html).toContain('title="27.48050683"'); expect(html).toContain('percentage points');
    expect(html).toContain('scope="col"'); expect(html).toContain('tabindex="0"');
  });

  it('retains the selected entry’s reference while live updates arrive and rejects late detail replacement', async () => {
    const { api, controller, push } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '100', step: 90, journalCount: 3, turnCount: 3 });
    let finish!: () => void;
    api.journal = (requestId, sessionId, generation) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '100', journal: { ...journal(1), observedStep: 30, firstAppliedStep: 31, measurementReference: { ...reference(30), previousStep: null, comparisonAvailable: false, rows: reference(30).rows.map(row => ({ ...row, previous: null, delta: null })) } } }); });
    const older = controller.selectJournal('journal-1');
    api.journal = async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '100', journal: { ...journal(2), observedStep: 60, firstAppliedStep: 61, measurementReference: reference() } });
    await controller.selectJournal('journal-2'); const accepted = controller.snapshot().journal;
    finish(); await older; push({ revision: '200', step: 120, journalCount: 4, turnCount: 4 }); await settle();
    expect(controller.snapshot().journal).toBe(accepted); expect(controller.snapshot().journal?.measurementReference?.currentStep).toBe(60);
    expect(controller.snapshot().frame?.step).toBe('120');
  });
});
