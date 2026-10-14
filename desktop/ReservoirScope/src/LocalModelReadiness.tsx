import { useEffect, useState, useSyncExternalStore } from 'react';
import { languageKey, localModelError, LocalModelController, type ModelReadinessState } from './localModelController';
import type { LanguageConfiguration } from './freshTypes';

export function ModelReadinessEvidence({ state }: { state: ModelReadinessState }) {
  const result = state.result;
  return <>{state.error && <p role="alert" className="fresh-error">{state.error}</p>}{state.message && <p role="status">{state.message}</p>}{result && <section className="model-readiness-receipt" aria-label="Selected local model readiness receipt"><strong>{result.status === 'found' ? 'Model identity found at this endpoint' : result.status === 'cancelled' ? 'Readiness check cancelled' : 'Model unavailable at this check'}</strong><dl><dt>Endpoint</dt><dd>{result.endpoint}</dd><dt>Requested model</dt><dd>{result.requestedModel}</dd><dt>Matched model</dt><dd>{result.matchedModel ?? 'No match retained'}</dd><dt>Retained digest</dt><dd className="fresh-hash">{result.digest ?? 'Not supplied by the service'}</dd><dt>Check time</dt><dd>{result.checkedAtMs} epoch milliseconds</dd><dt>Operation</dt><dd>{result.operationId}</dd></dl>{result.diagnostic && <p>{result.diagnostic}</p>}<p>This is availability and identity evidence at one check, not a memory-capacity or generation-success qualification. It starts no experiment and generates no text.</p></section>}</>;
}
export default function LocalModelReadiness({ configuration, disabled, controller: supplied, generationNote = 'Create validates configuration; Step, Run or a manual opportunity can send a generation request later.' }: { configuration: LanguageConfiguration; disabled: boolean; controller?: LocalModelController; generationNote?: string }) {
  const [owned] = useState(() => new LocalModelController()), controller = supplied ?? owned;
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot), key = languageKey(configuration), error = localModelError(configuration);
  useEffect(() => { controller.select(configuration); }, [controller, key]);
  useEffect(() => () => controller.dispose(), [controller]);
  return <section className="local-model-readiness"><p>Check contacts only the explicitly entered loopback endpoint. It neither starts a server nor downloads a model. {generationNote}</p>{error && <p className="fresh-small">{error}</p>}<div className="fresh-actions"><button type="button" disabled={disabled || !!error || state.checking} onClick={() => void controller.check(configuration)}>Check local model</button>{state.checking && <button type="button" onClick={() => void controller.cancel()}>Cancel readiness check</button>}</div>{state.key === key && <ModelReadinessEvidence state={state}/>}</section>;
}
