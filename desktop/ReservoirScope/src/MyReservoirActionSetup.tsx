import { useRef } from 'react';
import { CONTINUITY_CONTEXT_TOKENS, hasAuthoredActions, hasLocalInquiry, hasReservoirInputChoice, isActionPrompt, withAuthoredActionMode, withAuthoredActions } from './authoredActions';
import type { SustainedConfig, SustainedPromptVersion } from './myReservoirTypes';

export default function MyReservoirActionSetup({ config, setConfig }: { config: SustainedConfig; setConfig: (config: SustainedConfig) => void }) {
  const enabled = hasAuthoredActions(config);
  const ordinaryInvitation = useRef<SustainedPromptVersion | undefined>(isActionPrompt(config.promptVersion) ? 'reservoir-journal-v8' : config.promptVersion);
  return <section className="my-reservoir-action-setup" aria-label="Reservoir shaping setup">
    <h3>Reservoir shaping</h3>
    <label className="my-reservoir-check-in-toggle"><input type="checkbox" checked={enabled} onChange={event => {
      if (event.target.checked) ordinaryInvitation.current = config.promptVersion;
      setConfig(withAuthoredActions(config, event.target.checked, ordinaryInvitation.current));
    }}/>Let the model shape the reservoir</label>
    <p>After ordinary journal entries, the model can choose a state pulse, adjust how the reservoir evolves, release its adjustments, or leave controls unchanged.</p>
    {enabled && <>
      <label>Writing and action context<select value={config.actionMode} onChange={event => setConfig(withAuthoredActionMode(config, event.target.value as NonNullable<SustainedConfig['actionMode']>))}>
        <option value="authored-v3">Continuing inquiry and reservoir actions</option>
        <option value="authored-v2">Earlier actions and input choice</option>
        <option value="authored-v1">Earlier actions only</option>
      </select></label>
      {hasLocalInquiry(config) && <label>Control feedback<select value={config.controlFeedback ?? 'historical'} onChange={event => {
        const { controlFeedback: _feedback, ...base } = config;
        setConfig(event.target.value === 'diagnostic-v1' ? { ...base, controlFeedback: 'diagnostic-v1' } : base);
      }}><option value="diagnostic-v1">Specific correction feedback</option><option value="historical">Earlier feedback</option></select></label>}
      {config.controlFeedback === 'diagnostic-v1' && <p>Later entries receive specific formatting and value errors, a short quoted excerpt of the attempted control, and separate action, input and inquiry outcomes. Rejected text never becomes an executable command.</p>}
      <p>Adjustments persist until the model changes or releases them. Each action is saved with the entry, then its actual result returns with later writing. Releasing an adjustment preserves the state and history that developed.</p>
      {hasReservoirInputChoice(config) && <p>The model can also withhold an entry’s numerical text input independently of its action. The entry stays in the journal and can return as memory. Withholding replaces the previous held text input with zero; ordinary dynamics and any chosen action continue.</p>}
      {hasLocalInquiry(config) && <p>The model can send a bounded one-step input probe, keep an open question, and return to bounded evidence from its own reservoir and saved journal history. Meaningful interventions remain available beyond the recent action results. An inquiry is an opportunity to investigate, not a promise that the question has been answered.</p>}
      {hasLocalInquiry(config) && config.language.backend === 'ollama' && <p className="my-reservoir-small">Continuing inquiry uses {CONTINUITY_CONTEXT_TOKENS.toLocaleString('en-US')} context tokens by default to make room for retained evidence. Smaller contexts may omit supplied material. You can choose the context size in Advanced settings.</p>}
      <p className="my-reservoir-small">This choice is fixed when you create the session. Scheduled conversations still feed their writing back. Controls remain available in ordinary journal turns, but do not execute in the scheduled conversation itself.</p>
    </>}
  </section>;
}
