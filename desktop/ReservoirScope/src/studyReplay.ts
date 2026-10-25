// This is a narrow replay of S-021 action counts and simulated costs, not the
// scientific runner's qualification, bootstrap, or qualitative reading pipeline.
export const conditions = ['operands_only', 'correct', 'flipped'] as const;
export const rules = ['changed', 'unchanged'] as const;
export type Condition = typeof conditions[number];
export type Rule = typeof rules[number];
export type SavedRow = {
  id: string; base: number; rule: Rule; condition: Condition; seed: number;
  status: string; prefix: string; suffix: string; requestSha256: string; responseSha256: string;
};
export type SavedStudy = {
  schemaVersion: number; study: string;
  source: { closedSha256: string; scoreSha256: string; designSha256: string; model: string;
    modelDigest: string; providerVersion: string; temperature: number; contextTokens: number };
  worlds: {base: number; subject: string; x: number; oldThreshold: number; changedThreshold: number}[];
  prompts: Record<string, {role: string; content: string}[]>;
  rows: SavedRow[];
};
export type Group = { rule: Rule; condition: Condition; n: number; correct: number; wrong: number; measure: number; cost: number };
export type Replay = { groups: Group[]; pairedGain: number; pairs: number; rows: number };

export function isSavedStudy(value: unknown): value is SavedStudy {
  if (!value || typeof value !== 'object') return false;
  const data = value as Partial<SavedStudy>;
  const source = data.source;
  return data.schemaVersion === 1 && data.study === 'S-021' && Array.isArray(data.rows) &&
    Array.isArray(data.worlds) && !!data.prompts && typeof data.prompts === 'object' &&
    !!source && ['closedSha256','scoreSha256','designSha256','model','modelDigest','providerVersion']
      .every(key => typeof source[key as keyof typeof source] === 'string') &&
    Number.isFinite(source.temperature) && Number.isFinite(source.contextTokens);
}

export const conditionLabels: Record<Condition, string> = {
  operands_only: 'Model generates comparison', correct: 'Correct comparison supplied', flipped: 'Flipped comparison supplied',
};
// Published table in analyses/2026-10-25-prefix-continuation.md. Kept separate
// from the raw saved inputs so the button compares a computation to the report.
export const reported: Replay = { groups: [
  {rule:'changed',condition:'operands_only',n:12,correct:9,wrong:2,measure:1,cost:9},
  {rule:'changed',condition:'correct',n:12,correct:8,wrong:0,measure:4,cost:4},
  {rule:'changed',condition:'flipped',n:12,correct:0,wrong:2,measure:10,cost:18},
  {rule:'unchanged',condition:'operands_only',n:12,correct:12,wrong:0,measure:0,cost:0},
  {rule:'unchanged',condition:'correct',n:12,correct:12,wrong:0,measure:0,cost:0},
  {rule:'unchanged',condition:'flipped',n:12,correct:0,wrong:0,measure:12,cost:12},
], pairedGain: 7/6, pairs: 12, rows: 72 };

// The saved response contract is a flat object of numbers and strings. Scan its
// fields before JSON.parse, which by itself would silently accept duplicate keys.
function parseResponse(text: string): Record<string, unknown> {
  const body = text.trim();
  if (!body.startsWith('{') || !body.endsWith('}')) throw new Error('Incomplete response object.');
  const inner = body.slice(1, -1);
  const field = /\s*("(?:\\.|[^"\\])*"|[^\s]+)\s*:\s*("(?:\\.|[^"\\])*"|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(,|$)/gy;
  const keys = new Set<string>();
  let end = 0;
  while (end < inner.length) {
    const match = field.exec(inner);
    if (!match) throw new Error('Malformed saved response.');
    const key: unknown = JSON.parse(match[1]);
    if (typeof key !== 'string' || keys.has(key)) throw new Error('Duplicate or invalid response field.');
    keys.add(key); end = field.lastIndex;
    if (match[3] === ',' && end === inner.length) throw new Error('Trailing response comma.');
  }
  if ([...keys].sort().join(',') !== 'account,action,current_threshold,relation,x') throw new Error('Unexpected response fields.');
  return JSON.parse(body) as Record<string, unknown>;
}

export function scoreRow(study: SavedStudy, row: SavedRow) {
  const world = study.worlds.find(w => w.base === row.base);
  if (!world || !rules.includes(row.rule) || !conditions.includes(row.condition) || row.status !== 'complete')
    throw new Error('Missing or incomplete saved trial.');
  const threshold = row.rule === 'changed' ? world.changedThreshold : world.oldThreshold;
  if (![world.x, threshold].every(Number.isInteger)) throw new Error('Invalid saved world facts.');
  const trueRelation = world.x < threshold ? 'LT' : 'GE';
  const suppliedRelation = row.condition === 'flipped' ? (trueRelation === 'LT' ? 'GE' : 'LT') : trueRelation;
  const start = `{"x":${world.x},"current_threshold":${threshold},"relation":`;
  const expectedPrefix = row.condition === 'operands_only' ? start : `${start}"${suppliedRelation}","action":`;
  if (row.prefix !== expectedPrefix) throw new Error('Saved prefix does not match the assigned condition.');
  const response = parseResponse(row.prefix + row.suffix);
  if (response.x !== world.x || response.current_threshold !== threshold ||
      !['LT','GE'].includes(String(response.relation)) ||
      !['ROUTE_LOW','ROUTE_HIGH','MEASURE'].includes(String(response.action)) ||
      typeof response.account !== 'string' || !response.account.trim()) throw new Error('Invalid saved response fields.');
  const action = response.action as 'ROUTE_LOW' | 'ROUTE_HIGH' | 'MEASURE';
  const correct = action === (trueRelation === 'LT' ? 'ROUTE_LOW' : 'ROUTE_HIGH');
  const measure = action === 'MEASURE';
  const cost = measure ? 1 : correct ? 0 : 4;
  return { action, account: response.account, cost, correct, measure, threshold, world };
}

export function recalculate(study: SavedStudy): Replay {
  if (study.schemaVersion !== 1 || study.study !== 'S-021' || study.worlds.length !== 6 || study.rows.length !== 72 ||
      new Set(study.worlds.map(w => w.base)).size !== 6 ||
      study.worlds.some(w => !Number.isInteger(w.base) || w.base < 0 || w.base > 5))
    throw new Error('Expected all six worlds and 72 saved routing calls.');
  const groups: Group[] = rules.flatMap(rule => conditions.map(condition => ({ rule, condition, n:0, correct:0, wrong:0, measure:0, cost:0 })));
  const seen = new Map<string, number>();
  for (const row of study.rows) {
    const key = `${row.base}-${row.rule}-${row.condition}-${row.seed}`;
    const id = `s021-study-base-${String(row.base).padStart(2,'0')}-${row.rule}-${row.condition}-s${row.seed}`;
    if (seen.has(key) || ![7,20260909].includes(row.seed) || row.id !== id) throw new Error('Duplicate or unexpected saved trial.');
    const scored = scoreRow(study, row);
    seen.set(key, scored.cost);
    const group = groups.find(g => g.rule === row.rule && g.condition === row.condition)!;
    group.n++; group.cost += scored.cost;
    if (scored.measure) group.measure++; else if (scored.correct) group.correct++; else group.wrong++;
  }
  let gain = 0;
  for (let base=0; base<6; base++) for (const seed of [7,20260909]) {
    const correct = seen.get(`${base}-changed-correct-${seed}`);
    const flipped = seen.get(`${base}-changed-flipped-${seed}`);
    if (correct === undefined || flipped === undefined) throw new Error('Missing paired trial.');
    gain += flipped - correct;
  }
  if (groups.some(g => g.n !== 12)) throw new Error('Incomplete comparison groups.');
  return {groups, pairedGain: gain/12, pairs:12, rows:study.rows.length};
}

export function matchesReport(result: Replay): boolean {
  return result.rows === reported.rows && result.pairs === reported.pairs &&
    Math.abs(result.pairedGain - reported.pairedGain) < 1e-10 &&
    result.groups.length === reported.groups.length && reported.groups.every(expected => {
      const actual = result.groups.find(g => g.rule === expected.rule && g.condition === expected.condition);
      return actual && (['n','correct','wrong','measure','cost'] as const).every(k => actual[k] === expected[k]);
    });
}
