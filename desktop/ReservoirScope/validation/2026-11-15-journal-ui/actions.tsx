// Synthetic entry text and native test receipts. No provider or persisted writes.
import { createRoot } from 'react-dom/client';
import { useState } from 'react';
import MyReservoirJournals from '../../src/MyReservoirJournals';
import { journal, reservoirFixture, reservoirSummary } from '../../src/myReservoirTestFixtures';
import type { SustainedActionReceipt, SustainedJournal } from '../../src/myReservoirTypes';
import actions from '../../src/fixtures/experiments/experiment-actions.json';
import '../../src/styles.css';
import '../../src/myReservoir.css';
import '../../src/journalWorkspace.css';
import '../../src/desktopTheme.css';
const { controller } = reservoirFixture();
const retained = actions.state.recentReceipts[1] as SustainedActionReceipt;
function Preview() {
  const [model, setModel] = useState('gemma4:12b'), [outcome, setOutcome] = useState('measured');
  const receipt: SustainedActionReceipt = { ...retained, experiment: { ...retained.experiment!, outcome: outcome === 'noContrast' ? 'noContrast' : outcome === 'unresolved' ? 'unresolved' : 'measured' } };
  if (outcome === 'rejected') { receipt.status = 'rejected'; receipt.rejection = 'The requested direction is unavailable in the retained scan. Choose a current measured direction.'; receipt.experiment = { reportId: null, outcome: null, explanation: receipt.rejection }; }
  const body = 'This is synthetic journal prose. The action strip above refers to a retained native test receipt, rather than treating this paragraph as proof of execution.\n\nOpening the result should reveal the exact request and its recorded outcome. The full journal remains readable below it.';
  const entry: SustainedJournal = { ...journal(2), entryId: retained.journalId, text: body, configuredModel: model, action: { body, request: retained.request, rawTail: retained.rawTail, rejection: null }, actionReceipt: ['pending', 'skipped'].includes(outcome) ? null : receipt, status: outcome === 'pending' ? 'savedPendingApplication' : outcome === 'skipped' ? 'skipped' : 'applied' };
  if (['pending', 'skipped'].includes(outcome)) { entry.firstAppliedStep = null; entry.application = null; }
  const summary = reservoirSummary({ sessionId: 'synthetic-run-identity', step: 7, journalCount: 2, config: { ...reservoirSummary().config, language: { backend: 'ollama', model } } });
  const state = { ...controller.snapshot(), summary, journal: entry, journalRevision: '7', journalPosition: 2, followLatest: false, seenJournalCount: 2 };
  return <div className="app-shell"><header className="app-header"><strong>Synthetic action UI qualification</strong><label>Model <select value={model} onChange={e => setModel(e.target.value)}><option>gemma4:12b</option><option>glm-4.7-flash:latest</option><option>ministral-3:14b</option></select></label><label>Outcome <select value={outcome} onChange={e => setOutcome(e.target.value)}>{['measured', 'noContrast', 'unresolved', 'rejected', 'pending', 'skipped'].map(value => <option key={value}>{value}</option>)}</select></label></header><main><section className="my-reservoir journal-workspace"><MyReservoirJournals key={outcome} state={state} controller={controller}/></section></main></div>;
}
createRoot(document.getElementById('root')!).render(<Preview/>);
