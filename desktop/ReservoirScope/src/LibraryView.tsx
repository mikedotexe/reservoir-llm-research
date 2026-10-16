import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { errorText } from './api';
import { libraryApi } from './libraryApi';
import { DEFAULT_LIBRARY_QUERY, type LibraryCoverage, type LibraryEntry, type LibraryPage, type LibraryQuery } from './libraryTypes';
import { entryCanOpen, LIBRARY_ROW_HEIGHT, libraryDate, libraryHealth, visibleLibraryRows } from './libraryViewModel';
import type { OpenRecordResult } from './types';
import './library.css';

let sequence = 0;
const requestId = () => `library-${++sequence}`;

export default function LibraryView({ active, onOpen, onPreparationHistory }: { active: boolean; onPreparationHistory?: () => void; onOpen: (result: OpenRecordResult) => void }) {
  const [query, setQuery] = useState<LibraryQuery>({ ...DEFAULT_LIBRARY_QUERY });
  const [page, setPage] = useState<LibraryPage | null>(null);
  const [coverage, setCoverage] = useState<LibraryCoverage | null>(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [message, setMessage] = useState('');
  const [problem, setProblem] = useState('');
  const [queryProblem, setQueryProblem] = useState('');
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState<LibraryEntry | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const viewport = useRef<HTMLDivElement>(null);
  const lastLoadedQuery = useRef<LibraryQuery | null>(null);
  const requestGeneration = useRef(0);
  const openGeneration = useRef(0);
  const alive = useRef(true);
  const scanGeneration = useRef(0);

  useEffect(() => { alive.current = true; return () => { alive.current = false; openGeneration.current++; requestGeneration.current++; }; }, []);
  useEffect(() => { if (!active) openGeneration.current++; }, [active]);
  useEffect(() => {
    if (!active) return;
    const generation = ++requestGeneration.current;
    setLoading(true);
    const timer = window.setTimeout(() => {
      void libraryApi.query(query).then(result => {
        if (!alive.current || generation !== requestGeneration.current) return;
        setPage(result); setCoverage(result.coverage); setQueryProblem(''); setLoading(false);
        if (lastLoadedQuery.current !== query) setScrollTop(0);
        lastLoadedQuery.current = query;
      }).catch(error => {
        if (!alive.current || generation !== requestGeneration.current) return;
        setQueryProblem(errorText(error)); setLoading(false);
      });
    }, 180);
    return () => { window.clearTimeout(timer); requestGeneration.current++; };
  }, [active, query, revision]);

  useLayoutEffect(() => {
    if (active && viewport.current) viewport.current.scrollTop = scrollTop;
  }, [active, page, scrollTop]);

  useEffect(() => {
    if (!scanning) return;
    let pending = false; const generation=scanGeneration.current;
    const timer = window.setInterval(() => {
      if (pending) return; pending = true;
      void libraryApi.status().then(status => { if (alive.current && generation===scanGeneration.current) setCoverage(status); })
        .catch(error => { if (alive.current) setProblem(errorText(error)); }).finally(() => { pending = false; });
    }, 400);
    return () => window.clearInterval(timer);
  }, [scanning]);

  const filter = (patch: Partial<LibraryQuery>) => { setQuery(current => ({ ...current, ...patch, offset: 0 })); };
  const refresh = async (rebuild: boolean) => {
    if (working || scanning) return;
    scanGeneration.current++; setScanning(true); setProblem(''); setMessage(rebuild ? 'Rebuilding metadata from this application’s managed files…' : 'Refreshing managed files and bundled catalog…');
    try { const status = await libraryApi.scan(rebuild); if (alive.current) { setCoverage(status); setMessage(status.message); setRevision(value => value + 1); } }
    catch (error) { if (alive.current) setProblem(errorText(error)); }
    finally { scanGeneration.current++; if (alive.current) setScanning(false); }
  };
  const importRecord = async () => {
    if (working || scanning) return;
    setWorking(true); setProblem('');
    const request = requestId();
    try {
      const result = await libraryApi.importRecord(request);
      if (!alive.current) return;
      if (result.requestId !== request) throw new Error('Import response does not match its request.');
      setMessage(result.cancelled ? 'Import cancelled; nothing was added.' : result.published
        ? result.duplicate ? 'These exact bytes are already in your Library. The existing entry was retained.' : 'Verified original bytes were saved in your Library.'
        : 'No Library copy was published.');
      const diagnostics = [...result.diagnostics, ...(!result.published ? result.report?.diagnostics ?? [] : [])];
      setProblem(diagnostics.join('\n')); if (result.published) { setQuery(current => ({ ...current, offset: 0 })); setRevision(value => value + 1); }
    } catch (error) { if (alive.current) setProblem(errorText(error)); }
    finally { if (alive.current) setWorking(false); }
  };
  const open = async (entry: LibraryEntry) => {
    if (working) return;
    const generation = ++openGeneration.current, request = requestId();
    setWorking(true); setProblem(''); setMessage('Verifying the selected recording before opening…');
    let transferred = false; let result: OpenRecordResult | null = null;
    try {
      result = await libraryApi.open(request, entry.id);
      if (!alive.current || generation !== openGeneration.current) return;
      if (result.requestId !== request) throw new Error('Open response does not match its request.');
      if (!result.record || result.report?.status !== 'passed') {
        setProblem(result.report?.diagnostics.join('\n') || 'This entry could not be verified. Refresh for current diagnostics.');
        setMessage('The current reading is unchanged.'); return;
      }
      onOpen(result); transferred = true; setRevision(value => value + 1); setMessage('Verified recording opened. No model was contacted.');
    } catch (error) { if (alive.current && generation === openGeneration.current) setProblem(errorText(error)); }
    finally {
      if (!transferred && result?.record) void libraryApi.release(result.record.recordId).catch(() => {});
      if (alive.current) setWorking(false);
    }
  };
  if (!active) return null;
  const entries = page?.entries ?? [];
  const visible = visibleLibraryRows(entries.length, scrollTop, 570);
  const shown = entries.slice(visible.first, visible.last);
  return <section className="library-workspace" aria-labelledby="library-title">
    <div className="library-heading"><div><h1 id="library-title">Library</h1><p>Included examples and your saved recordings. Import adds a verified copy; opening a recording never runs a model.</p></div><button className="primary-button" disabled={working || scanning} onClick={() => void importRecord()}>Import recording…</button></div>
    <div className="library-tools"><button disabled={working || scanning} onClick={() => void refresh(false)}>Refresh</button><button disabled={working || scanning} onClick={() => void refresh(true)}>Rebuild index</button>{scanning && <button onClick={() => void libraryApi.cancel().then(setCoverage).catch(error => setProblem(errorText(error)))}>Stop scan</button>}<label className="library-search">Search recordings<input type="search" value={query.text} maxLength={4096} placeholder="Title, file, stage, model, seed or ID" aria-describedby="library-search-scope" onChange={event => filter({ text: event.target.value })} /></label></div>
    <p id="library-search-scope" className="library-order">Search covers recording details, not journal text.</p>
    <div className="library-filters">
      <Filter label="Origin" value={query.origin} values={['all', 'bundled', 'managed', 'created']} onChange={origin => filter({ origin })} />
      <Filter label="Experiment type" value={query.family} values={['all', 'stage', 'actions', 'exploration', 'regulation', 'unknown']} onChange={family => filter({ family })} />
      <Filter label="Recorded source" value={query.source} values={['all', 'scripted', 'model', 'fixedReplay', 'numerical', 'unknown']} onChange={source => filter({ source })} />
      <Filter label="Outcome" value={query.outcome} values={['all', 'completed', 'stopped', 'failed', 'snapshot', 'unknown']} onChange={outcome => filter({ outcome })} />
      <label><input type="checkbox" checked={query.recentOnly} onChange={event => filter({ recentOnly: event.target.checked })} />Recently opened</label>
      <label><input type="checkbox" checked={query.diagnosticsOnly} onChange={event => filter({ diagnosticsOnly: event.target.checked })} />Needs attention</label>
    </div>
    <div className={`library-coverage ${coverage?.complete ? 'complete' : ''}`} role="status"><strong>{scanning ? 'Scanning the Library…' : coverage?.complete ? 'Last scan complete' : 'Library scan incomplete'}</strong><span>{coverage?.message ?? 'Waiting for the Library.'}</span>{coverage && <small>{coverage.examined.toLocaleString()} directory entries examined · {coverage.indexed.toLocaleString()} indexed · {coverage.diagnosticCount.toLocaleString()} diagnostics{coverage.finishedAtMs !== null ? ` · ${libraryDate(coverage.finishedAtMs)}` : ''}</small>}</div>
    {message && <p role="status">{message}</p>}{(problem || queryProblem) && <div className="library-error" role="alert">{[problem,queryProblem].filter(Boolean).join("\n")}<p>Previous results remain visible. An index error does not erase saved recordings.</p></div>}
    <div className="library-results-heading"><h2>{query.recentOnly ? 'Recently opened' : 'Recordings'}</h2><span>{loading ? 'Loading recordings…' : page ? `${page.total.toLocaleString()} matching entries` : 'No results loaded'}</span></div>
    <p className="library-order">Bundled examples follow the authored catalog order. Managed recordings use local save/import time, then stable identity. Dates here are local bookkeeping, not authenticated experiment time.</p>
    {entries.length > 0 ? <div className="library-viewport" ref={viewport} tabIndex={0} role="region" aria-label="Recording results. Scroll for more rows; use next page for more results." onScroll={event => setScrollTop(event.currentTarget.scrollTop)}>
      <div style={{ height: entries.length * LIBRARY_ROW_HEIGHT, position: 'relative' }}>
        <div style={{ position: 'absolute', top: visible.top, left: 0, right: 0 }}>
          {shown.map(entry => <article key={entry.id} className={`library-row ${selected?.id === entry.id ? 'selected' : ''}`} style={{ height: LIBRARY_ROW_HEIGHT }}>
            <div><h3>{entry.title}</h3><p className="library-filename" title={entry.filename}>{entry.filename}</p><p>{entry.origin === 'bundled' ? 'Bundled · read-only' : `${entry.origin === 'created' ? 'Created here' : entry.savedAtMs === null ? 'Managed · origin unavailable' : 'Imported'} · saved ${libraryDate(entry.savedAtMs)}`} · {entry.family} · {entry.outcome}</p><p className={entry.diagnostic ? 'library-row-warning' : 'library-health'}>{libraryHealth(entry)}</p></div>
            <div className="library-row-actions"><button onClick={() => setSelected(entry)}>Details</button><button disabled={working || !entryCanOpen(entry)} onClick={() => void open(entry)}>Verify & open</button></div>
          </article>)}
        </div>
      </div>
    </div> : <div className="library-no-results">{page ? page.coverage.complete ? 'No entries match these filters.' : 'No indexed entries match yet. Coverage is incomplete; refresh before treating this as an empty Library.' : 'The Library has not returned a usable index. Check the diagnostic above.'}</div>}
    <nav className="library-pagination" aria-label="Library pages"><button disabled={loading || query.offset === 0} onClick={() => setQuery(current => ({ ...current, offset: Math.max(0, current.offset - current.limit) }))}>Previous page</button><span>{page ? `${page.total === 0 ? 0 : page.offset + 1}–${Math.min(page.offset + page.entries.length, page.total)} of ${page.total}` : 'Not loaded'}</span><button disabled={loading || !page?.hasMore} onClick={() => setQuery(current => ({ ...current, offset: current.offset + current.limit }))}>Next page</button></nav>
    {selected && <section className="library-detail" aria-label="Selected recording metadata"><button onClick={() => setSelected(null)}>Close details</button><h2>{selected.title}</h2><p>{libraryHealth(selected)}</p>{selected.diagnostic && <p className="library-error">{selected.diagnostic}</p>}<dl>{Object.entries({ Filename: selected.filename, Format: selected.format, 'Library identity': selected.id, 'SHA-256': selected.sha256 ?? 'Unknown', 'Embedded ID': selected.embeddedId ?? 'Not recorded', Seed: selected.seed ?? 'Unknown', 'Recorded source': selected.source, 'Configured backend': selected.backend, 'Configured model': selected.model, Outcome: selected.outcome, 'Local save/import': libraryDate(selected.savedAtMs), 'Last opened': libraryDate(selected.lastOpenedAtMs) }).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></section>}
    <details className="library-storage"><summary>Storage and recovery</summary><p>Original recordings are separate from the rebuildable SQLite index. Import verifies a bounded snapshot and preserves exact bytes. Search covers metadata; journal-body search is not included. Recorded source describes retained turn/request metadata, not authenticated provider activity. Fixed replay is separate from a configured model; records without turn/request evidence have an unknown source.</p><p>Refresh inspects only this application’s managed files and immutable bundled catalog. Unsupported, missing or unreadable entries stay visible with diagnostics. Rebuild preserves scientific files and archives the old index.</p><code>{page?.storagePath ?? 'App-specific local Library path unavailable'}</code></details>
    {onPreparationHistory && <section className="library-history"><h2>Preparation history</h2><p>Read the original attempts, correction and later retry together.</p><button onClick={onPreparationHistory}>Open preparation history in Observatory</button></section>}
  </section>;
}
function Filter({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  return <label>{label}<select value={value} onChange={event => onChange(event.target.value)}>{values.map(option => <option value={option} key={option}>{option === 'all' ? 'All' : option === 'fixedReplay' ? 'Fixed replay' : option === 'managed' ? 'Imported / other managed' : option === 'created' ? 'Created here' : option}</option>)}</select></label>;
}
