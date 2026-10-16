import { useEffect, useState, useSyncExternalStore } from 'react';
import { languageKey, localModelError, LocalModelController, type ModelReadinessState } from './localModelController';
import type { LanguageConfiguration } from './freshTypes';

export function ModelReadinessEvidence({ state }: { state: ModelReadinessState }) {
  const result = state.result;
  return <>{state.error && <p role="alert" className="fresh-error">{state.error}</p>}{state.message && <p role="status">{state.message}</p>}{result && <section className="model-readiness-receipt" aria-label="Local model check"><strong>{result.status === 'found' ? 'Model available' : result.status === 'cancelled' ? 'Model check cancelled' : 'Model unavailable'}</strong><dl><dt>Server address</dt><dd>{result.endpoint}</dd><dt>Requested model</dt><dd>{result.requestedModel}</dd><dt>Matched model</dt><dd>{result.matchedModel ?? 'No match retained'}</dd></dl>{result.diagnostic && <p>{result.diagnostic}</p>}<p>This checks availability only; it generates no text and does not guarantee enough memory or a successful response.</p><details><summary>Check details</summary><dl><dt>Model digest</dt><dd className="fresh-hash">{result.digest ?? 'Not supplied by the service'}</dd><dt>Check time</dt><dd>{result.checkedAtMs} epoch milliseconds</dd><dt>Operation</dt><dd>{result.operationId}</dd></dl></details></section>}</>;
}
export default function LocalModelReadiness({ configuration, disabled, controller: supplied, generationNote = 'Create saves the settings. Step, Run or a manual writing request may contact the model later.' }: { configuration: LanguageConfiguration; disabled: boolean; controller?: LocalModelController; generationNote?: string }) {
  const [owned] = useState(() => new LocalModelController()), controller = supplied ?? owned;
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot), key = languageKey(configuration), error = localModelError(configuration);
  useEffect(() => { controller.select(configuration); }, [controller, key]);
  useEffect(() => () => controller.dispose(), [controller]);
  return <section className="local-model-readiness"><p>Check contacts the local server address above. It does not start a server or download a model. {generationNote}</p>{error && <p className="fresh-small">{error}</p>}<div className="fresh-actions"><button type="button" disabled={disabled || !!error || state.checking} onClick={() => void controller.check(configuration)}>Check local model</button>{state.checking && <button type="button" onClick={() => void controller.cancel()}>Cancel model check</button>}</div>{state.key === key && <ModelReadinessEvidence state={state}/>}</section>;
}
