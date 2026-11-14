import { useRef } from 'react';
import { ACTION_JOURNAL_PROMPT, withAuthoredActions } from './authoredActions';
import type { SustainedConfig, SustainedPromptVersion } from './myReservoirTypes';

export default function MyReservoirActionSetup({ config, setConfig }: { config: SustainedConfig; setConfig: (config: SustainedConfig) => void }) {
  const enabled = config.actionMode === 'authored-v1';
  const ordinaryInvitation = useRef<SustainedPromptVersion | undefined>(config.promptVersion === ACTION_JOURNAL_PROMPT ? 'reservoir-journal-v8' : config.promptVersion);
  return <section className="my-reservoir-action-setup" aria-label="Reservoir shaping setup">
    <h3>Reservoir shaping</h3>
    <label className="my-reservoir-check-in-toggle"><input type="checkbox" checked={enabled} onChange={event => {
      if (event.target.checked) ordinaryInvitation.current = config.promptVersion;
      setConfig(withAuthoredActions(config, event.target.checked, ordinaryInvitation.current));
    }}/>Let the model shape the reservoir</label>
    <p>After ordinary journal entries, the model can choose a state pulse, adjust how the reservoir evolves, release its adjustments, or leave controls unchanged.</p>
    {enabled && <>
      <p>Adjustments persist until the model changes or releases them. Each action is saved with the entry, then its actual result returns with later writing. Releasing an adjustment preserves the state and history that developed.</p>
      <p className="my-reservoir-small">This choice is fixed when you create the session. Scheduled conversations still feed their writing back, but do not execute actions.</p>
    </>}
  </section>;
}
