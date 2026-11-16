import { useEffect, useRef, useState } from 'react';
import type { SustainedConfig, SustainedJournal } from './myReservoirTypes';
import { JournalActionDetails } from './MyReservoirActions';
import { journalActionSummary } from './journalActionSummary';
import { actionResultReference, loadJournalActionResult, type JournalSession, type MatchedActionResult } from './journalActionResult';
import { CompactScanView, QuestionView, ScanView } from './MyReservoirSonar';
import { ExperimentView } from './MyReservoirExperiments';

export default function JournalActionStrip({ journal, config, session }: { journal: SustainedJournal; config?: SustainedConfig; session?: JournalSession }) {
  const summary = journalActionSummary(journal, config), reference = actionResultReference(journal.actionReceipt);
  const [result, setResult] = useState<MatchedActionResult | null>(null), [busy, setBusy] = useState(false), [message, setMessage] = useState('');
  const ticket = useRef(0);
  useEffect(() => { ticket.current++; setResult(null); setBusy(false); setMessage(''); return () => { ticket.current++; }; }, [journal.entryId, session?.sessionId, session?.generation]);
  async function loadResult() {
    if (!session || !reference) return;
    const current = ++ticket.current;
    setBusy(true); setMessage('');
    try {
      const match = await loadJournalActionResult(session, reference);
      if (current !== ticket.current) return;
      setResult(match);
      if (!match) setMessage('These measurements are no longer in the retained result cache. The saved receipt and result identity remain below; no newer result has been substituted.');
    } catch (error) { if (current === ticket.current) setMessage(error instanceof Error ? error.message : String(error)); }
    finally { if (current === ticket.current) setBusy(false); }
  }
  const strip = <><strong>{summary.label}</strong>{summary.scope && <span className="journal-action-scope">{summary.scope}</span>}<span className="journal-action-outcome" data-tone={summary.tone}>{summary.status}</span></>;
  if (!summary.expandable) return <div className="journal-action-strip journal-action-passive" aria-label="Entry action status">{strip}</div>;
  return <details className="journal-action-strip">
    <summary aria-label={`${summary.label} · ${summary.status} · ${summary.status === 'Rejected' ? 'View reason' : journal.actionReceipt ? 'View result' : 'View choice'}`}>{strip}<span className="journal-action-open">{summary.status === 'Rejected' ? 'View reason' : journal.actionReceipt ? 'View result' : 'View choice'}</span></summary>
    <div className="journal-action-expanded">
      {reference && <div className="journal-action-measurements"><p className="sonar-id">Result {reference.id}</p>
        {session && !result && <button disabled={busy} onClick={() => void loadResult()}>{busy ? 'Loading saved measurements…' : 'Load matching measurements'}</button>}
        {message && <p role="status">{message}</p>}
        {result?.kind === 'experiment' && <ExperimentView report={result.report}/>}
        {result?.kind === 'compact' && <CompactScanView view={result.view} label="This entry’s saved scan"/>}
        {result?.kind === 'question' && <QuestionView report={result.report} label="This entry’s saved comparison"/>}
        {result?.kind === 'scan' && <ScanView report={result.report} label="This entry’s saved scan"/>}
      </div>}
      <JournalActionDetails journal={journal}/>
      {journal.action?.request && <details><summary>Requested parameters</summary><pre>{JSON.stringify(journal.action.request, null, 2)}</pre></details>}
    </div>
  </details>;
}
