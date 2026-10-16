export interface ReadingEntry {
  id: string; status: 'complete' | 'incomplete'; text: string; sha256: string;
  observedStep: number; savedStep: number | null; appliedStep: number | null;
  requestId: string; prompt: string; promptSha256: string; stopReason: string;
  contentTokens: number; sourceResponseSha256: string; eventIds: string[];
}
export interface ReadingEvent { id: string; kind: string; step: number; observation: string | null }
export interface ReadingDisclosure {
  arm: 'no_steering' | 'decaying_trace' | 'recurrent'; sourceAttempt: string; sourceSession: string;
  sourceFormat: string; recordSha256: string; modelManifestSha256: string; calibrationSha256: string;
  modelId: string; modelRevision: string;
  protocol: { seed: number; stepsBetween: number; journalEvery: number; maxJournalTokens: number; gain: number };
  notes: { title: string; text: string; sha256: string; sourceSha256: string; attribution: string }[];
}
export interface CollectionReading { id: string; entries: ReadingEntry[]; events: ReadingEvent[]; disclosure: ReadingDisclosure }
export interface ReadingCollection {
  format: 'activation-reading-collection-v1'; title: string; scope: string; questions: string[]; readings: CollectionReading[];
}
export interface OpenedReadingCollection { collectionId: string; sha256: string; collection: ReadingCollection }
export interface ActivationReadingApi {
  open(bundled: boolean): Promise<OpenedReadingCollection | null>;
  export(collectionId: string): Promise<{ name: string; sizeBytes: number; sha256: string } | null>;
  close(collectionId: string): Promise<void>;
}
