import type { SustainedSummary } from './myReservoirTypes';

export function runIdentity(summary: Pick<SustainedSummary, 'sessionId' | 'config'>) {
  const language = summary.config.language;
  const model = language.backend === 'ollama' ? language.model || 'Model not specified' : 'Scripted writing';
  const family = model.toLowerCase().split('/').at(-1)!;
  const accent = language.backend !== 'ollama' ? 'scripted' : /^gemma/.test(family) ? 'gemma'
    : /^glm/.test(family) ? 'glm' : /^(mistral|ministral|magistral)/.test(family) ? 'mistral' : 'other';
  // Display abbreviation only. The full stored identity remains in the tooltip and evidence.
  let hash = 2166136261;
  for (const character of summary.sessionId) hash = Math.imul(hash ^ character.codePointAt(0)!, 16777619);
  const shortId = (hash >>> 0).toString(16).padStart(8, '0');
  return { model, accent, label: `${summary.config.peerReading?.participant ? `${summary.config.peerReading.participant} · ` : ''}Run ${shortId}` };
}

export default function RunIdentity({ summary }: { summary: SustainedSummary }) {
  const identity = runIdentity(summary);
  return <div className="run-identity" data-model-family={identity.accent} aria-label="Run identity">
    <span className="run-model" title={`Configured model: ${identity.model}`}><i aria-hidden="true"/>{identity.model}</span>
    <span className="run-label" title={`Session ${summary.sessionId} · generation ${summary.generation}`}>{identity.label}</span>
  </div>;
}
