// Inert, local UI qualification. No provider, persisted session or app commands.
import { createRoot } from 'react-dom/client';
import { useState } from 'react';
import MyReservoir from '../../src/MyReservoir';
import { reservoirFixture, journal, settle } from '../../src/myReservoirTestFixtures';
import { DEFAULT_SUSTAINED_CONFIG } from '../../src/myReservoirTypes';
import { DEFAULT_CHECK_IN_SCHEDULE, withCheckInCapacity } from '../../src/checkInSchedule';
import '../../src/styles.css';
import '../../src/journalWorkspace.css';

const fixture = reservoirFixture();
const { controller, push, api } = fixture;
const read = api.journal;
api.journal = async (...args) => {
  await new Promise(resolve => setTimeout(resolve, 250));
  const result = await read(...args);
  return { ...result, journal: { ...result.journal, text: Array.from({ length: 18 }, (_, i) => `Paragraph ${i + 1}. This is synthetic reading material for entry ${result.journal.turnId}. The visible journal should stay still while another entry arrives. The measured state is distinct from its description; a small change in fill remains a percentage change, not a discovery of topology.`).join('\n\n') } };
};
await controller.create(withCheckInCapacity({ ...DEFAULT_SUSTAINED_CONFIG, checkInSchedule: DEFAULT_CHECK_IN_SCHEDULE }));
await controller.action('start');
push({ revision: '20', phase: 'awaitingLanguage', step: 90, durableStep: 90, journalCount: 3, turnCount: 3, elapsedSeconds: 3615, canStart: false, canPause: true,
  pendingLanguage: { operationId: 'fixture-only', turnId: 4, attemptId: 4, observedStep: 90, endpoint: '', model: '', state: 'requesting' },
  checkIns: { intervalSeconds: 3600, endAfterSeconds: 21600, settings: { ...DEFAULT_CHECK_IN_SCHEDULE, revision: 0 }, slots: Array.from({ length: 6 }, (_, i) => ({ ordinal: i + 1, scheduledSeconds: (i + 1) * 3600, status: i ? 'pending' : 'applied', entryId: i ? null : journal(1).entryId, appliedStep: i ? null : 4 })), canEdit: false, complete: false },
});
function Preview() {
  const [report, setReport] = useState('Synthetic fixture · no model calls'), [busy, setBusy] = useState(false);
  const append = async () => {
    setBusy(true);
    const pane = document.querySelector('.journal-reader-pane')!, article = pane.querySelector('article');
    const before = { page: window.scrollY, reader: pane.scrollTop, top: pane.getBoundingClientRect().top, entry: controller.snapshot().journal?.entryId };
    const state = controller.snapshot(), count = state.summary!.journalCount;
    push({ revision: String(Number(state.summary!.revision) + 1), journalCount: count + 1, turnCount: count + 1 });
    await settle(); await new Promise(resolve => setTimeout(resolve, 400));
    setReport(JSON.stringify({ before, after: { page: window.scrollY, reader: pane.scrollTop, top: pane.getBoundingClientRect().top, entry: controller.snapshot().journal?.entryId }, samePane: pane === document.querySelector('.journal-reader-pane'), sameArticle: article === pane.querySelector('article'), followLatest: controller.snapshot().followLatest }));
    setBusy(false);
  };
  return <div className="app-shell"><header className="app-header"><div className="brand"><strong>Reservoir Scope</strong></div><span>Synthetic UI qualification</span></header><main><MyReservoir active controller={controller}/></main><div style={{ position: 'fixed', left: 12, bottom: 8, zIndex: 60, maxWidth: 'calc(100vw - 24px)', background: '#203238', padding: 8, fontSize: 11 }}><button disabled={busy} onClick={() => void append()}>Append synthetic entry</button><output aria-label="Reading stability result" style={{ marginLeft: 10 }}>{report}</output></div></div>;
}
createRoot(document.getElementById('root')!).render(<Preview/>);
