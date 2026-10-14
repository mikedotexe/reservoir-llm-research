// Validation-only UI fixture. No Tauri backend, actual session, file store or model.
import { createRoot } from 'react-dom/client';
import MyReservoir from '../../src/MyReservoir';
import { DEFAULT_SUSTAINED_CONFIG } from '../../src/myReservoirTypes';
import { journal, reservoirFixture, settle } from '../../src/myReservoirTestFixtures';
import '../../src/styles.css';

const fixture = reservoirFixture();
fixture.api.journal = async (requestId, sessionId, generation, entryId) => ({
  requestId, sessionId, generation, revision: '30', journal: {
    ...journal(Number(entryId.split('-')[1])),
    text: 'This is synthetic prose for a reading-layout check. The current observation gives me a set of coordinates and a separate fill measurement. I can describe what was supplied without pretending that either tells the whole story.\n\nThe next observation can show how the state developed after this writing was returned as input. Its path also depends on the reservoir’s recurrence, forcing and noise.\n\nI will leave this entry here and return to the next observation.',
  },
});
const scenario = new URLSearchParams(location.search).get('scenario');
if (scenario) {
  await fixture.controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
  await fixture.controller.action('start');
  fixture.push({ revision: '30', phase: 'running', step: 90, durableStep: 90, simulatedTime: 30, elapsedSeconds: 3721.8, journalCount: 3, turnCount: 3, usedBytes: 1245000, canPause: true, canStart: false });
  await fixture.controller.journals(); await fixture.controller.selectJournal('journal-1');
  if (scenario === 'blocked') fixture.push({ revision: '31', phase: 'storageBlocked', canPause: false, canStart: false, canRetrySave: true, canSkipFeedback: true, pendingSave: { entryId: 'owned-pending-fixture', observedStep: 90, attemptId: 4 }, diagnostics: ['The journal could not be saved. Check the selected storage location, then retry.'] });
}
createRoot(document.getElementById('root')!).render(<main style={{ padding: 24, maxWidth: 1100, margin: 'auto' }}><p style={{ fontSize: 12, color: '#d9bd7e' }}>UI fixture · simulated state and synthetic prose · no live session or model</p><nav style={{ display: 'flex', gap: 20, marginBottom: 20 }}><a href="?">Setup</a><a href="?scenario=running">Reading</a><a href="?scenario=blocked">Save failure</a></nav><MyReservoir active controller={fixture.controller}/></main>);
