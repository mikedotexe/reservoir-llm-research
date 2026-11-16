import type { SustainedAuthoredRequest, SustainedConfig, SustainedJournal } from './myReservoirTypes';

const kinds: Record<SustainedAuthoredRequest['kind'], [string, string]> = {
  experiment: ['Experiment', 'On copies'], scan: ['Scan', 'On copies'], scanQuestion: ['Question scan', 'On copies'],
  probeExperiment: ['Experiment probe', 'Live input'], probeScan: ['Scan probe', 'Live input'], probe: ['Input probe', 'Live input'],
  pulse: ['State pulse', 'Live state'], tune: ['Tune', 'Controls'], release: ['Release', 'Controls'],
  readPeers: ['Read peers', 'Peer history'], none: ['NONE', 'No intervention'],
};
export const experimentOutcomeLabel = { measured: 'Measurements completed', noContrast: 'No distinguishing contrast', noExcitation: 'No probe stimulus', unresolved: 'Response unresolved' };
export function journalActionSummary(journal: SustainedJournal, config?: SustainedConfig) {
  const decision = journal.action, receipt = journal.actionReceipt;
  if (journal.checkIn) return { label: journal.checkIn.operatorId ? 'Custom conversation' : 'Scheduled conversation', scope: '', status: 'Actions off', tone: 'neutral', expandable: false };
  if (!decision) return { label: 'NEXT', scope: '', status: config && !config.actionMode ? 'Actions off' : 'No action record', tone: 'neutral', expandable: false };
  const request = decision.request, [label, scope] = request ? kinds[request.kind] : ['NEXT', ''];
  const base = { label, scope, expandable: true };
  if (journal.status === 'skipped') return { ...base, status: 'Skipped', tone: 'neutral' };
  if (receipt?.status === 'rejected' || decision.rejection) return { ...base, status: 'Rejected', tone: 'attention' };
  if (!receipt) return { ...base, status: journal.status === 'savedPendingApplication' ? 'Awaiting execution' : 'Outcome unavailable', tone: 'pending' };
  if (receipt.status === 'unchanged') return { ...base, status: 'No additional intervention', tone: 'neutral' };
  if (request?.kind === 'experiment') return { ...base, status: receipt.experiment?.outcome ? experimentOutcomeLabel[receipt.experiment.outcome] : 'Result unavailable', tone: receipt.experiment?.outcome === 'measured' ? 'recorded' : 'neutral' };
  if (request?.kind === 'scan') return { ...base, status: receipt.sonarScan ? 'Scan saved' : 'Result unavailable', tone: 'recorded' };
  if (request?.kind === 'scanQuestion') return { ...base, status: receipt.sonarQuestion ? 'Comparison saved' : 'Result unavailable', tone: 'recorded' };
  if (request?.kind === 'readPeers') {
    const count = receipt.peerRead?.snapshot.peers.filter(peer => peer.entry !== null).length;
    return { ...base, status: count === undefined ? 'Result unavailable' : count === 0 ? 'No peer entries available' : `${count} peer ${count === 1 ? 'entry' : 'entries'} captured`, tone: 'neutral' };
  }
  return { ...base, status: `Applied · step ${receipt.appliedStep}`, tone: 'recorded' };
}
