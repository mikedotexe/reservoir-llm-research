export type ActivationSetupState = 'missing' | 'preparing' | 'interrupted' | 'ready' | 'failed' | 'unsupported';

/** Recipient-local setup only. This receipt does not qualify model generation. */
export interface ActivationSetupStatus {
  state: ActivationSetupState;
  phase: string;
  message: string;
  downloadedBytes?: number | null;
  totalBytes?: number | null;
  requiredBytes?: number | null;
  pythonPath?: string | null;
  modelPath?: string | null;
  setupId?: string | null;
  canResume: boolean;
}

export interface ActivationRuntimePaths {
  pythonPath: string;
  modelPath: string;
}

export interface ActivationSetupApi {
  status(): Promise<ActivationSetupStatus>;
  prepare(resume: boolean): Promise<ActivationSetupStatus>;
  cancel(): Promise<ActivationSetupStatus>;
}

export interface ActivationSetupViewState {
  status: ActivationSetupStatus | null;
  pending: 'prepare' | 'resume' | 'cancel' | null;
  checking: boolean;
  error: string;
}

export function activationSetupCanPrepare(status: ActivationSetupStatus | null): boolean {
  return !!status && !status.canResume && (status.state === 'missing' || status.state === 'failed');
}

export function activationSetupCanResume(status: ActivationSetupStatus | null): boolean {
  return !!status?.canResume && (status.state === 'interrupted' || status.state === 'failed');
}

export function validateActivationSetupStatus(value: ActivationSetupStatus): void {
  if (!value || !['missing', 'preparing', 'interrupted', 'ready', 'failed', 'unsupported'].includes(value.state)
    || typeof value.phase !== 'string' || typeof value.message !== 'string' || typeof value.canResume !== 'boolean'
    || [value.downloadedBytes, value.totalBytes, value.requiredBytes].some(n => n !== undefined && n !== null && (!Number.isSafeInteger(n) || n < 0))
    || [value.pythonPath, value.modelPath, value.setupId].some(s => s !== undefined && s !== null && typeof s !== 'string')
    || value.state === 'ready' && (!value.pythonPath?.startsWith('/') || !value.modelPath?.startsWith('/'))
    || value.canResume && value.state !== 'interrupted' && value.state !== 'failed') {
    throw new Error('The activation setup status is invalid. Check setup again before continuing.');
  }
}
