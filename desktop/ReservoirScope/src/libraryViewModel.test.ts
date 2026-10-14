import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import LibraryView from './LibraryView';
import { entryCanOpen, libraryDate, libraryHealth, visibleLibraryRows, LIBRARY_ROW_HEIGHT } from './libraryViewModel';
import { DEFAULT_LIBRARY_QUERY, type LibraryEntry } from './libraryTypes';
import { libraryApi } from './libraryApi';

const ipc=vi.hoisted(()=>({enabled:false,invoke:vi.fn()}));
vi.mock('@tauri-apps/api/core',()=>({isTauri:()=>ipc.enabled,invoke:ipc.invoke}));
beforeEach(()=>{ipc.enabled=false;ipc.invoke.mockReset();});
const row=(health:string)=>({health} as LibraryEntry);
describe('Library presentation and bounded IPC',()=>{
  it('virtualizes large pages without making the later rows unreachable',()=>{
    expect(visibleLibraryRows(5001,0,570)).toEqual({first:0,last:8,top:0});
    const later=visibleLibraryRows(5001,4995*LIBRARY_ROW_HEIGHT,570);
    expect(later.first).toBe(4992);expect(later.last).toBe(5001);expect(later.top).toBe(4992*LIBRARY_ROW_HEIGHT);
    expect(visibleLibraryRows(0,99999,570)).toEqual({first:0,last:0,top:0});
    expect(visibleLibraryRows(2,-20,570)).toEqual({first:0,last:2,top:0});
  });
  it('separates indexed metadata from replay verification and unknown dates',()=>{
    expect(libraryDate(null)).toBe('Unknown');
    expect(libraryHealth(row('unverified'))).toContain('opening verifies');
    expect(libraryHealth(row('ready'))).toContain('opening verifies again');
    expect(libraryHealth(row('notBundled'))).toContain('not included');
    for(const health of ['ready','unverified','metadataIssue'])expect(entryCanOpen(row(health))).toBe(true);
    for(const health of ['damaged','missing','unsupported','unreadable','notBundled'])expect(entryCanOpen(row(health))).toBe(false);
  });
  it('does not fabricate a Library or invoke storage in browser preview',async()=>{
    await expect(libraryApi.query(DEFAULT_LIBRARY_QUERY)).rejects.toThrow('browser preview');
    await expect(libraryApi.importRecord('import')).rejects.toThrow('desktop app');
    expect(ipc.invoke).not.toHaveBeenCalled();
    const html=renderToStaticMarkup(createElement(LibraryView,{active:true,onOpen:()=>{}}));
    expect(html).toContain('No completed query');expect(html).toContain('Coverage incomplete');
    expect(html).not.toContain('Last scan complete');
  });
  it('routes opaque identities and explicit imports without exposing path authority',async()=>{
    ipc.enabled=true;ipc.invoke.mockResolvedValue({});
    await libraryApi.query({...DEFAULT_LIBRARY_QUERY,offset:5000,text:"' OR 1=1"});
    await libraryApi.open('r1','sha256:'+'f'.repeat(64));
    await libraryApi.importRecord('r2');await libraryApi.scan(true);await libraryApi.cancel();await libraryApi.release('handle');
    expect(ipc.invoke.mock.calls).toEqual([
      ['library_query',{query:{...DEFAULT_LIBRARY_QUERY,offset:5000,text:"' OR 1=1"}}],
      ['library_open',{requestId:'r1',entryId:'sha256:'+'f'.repeat(64)}],
      ['library_import',{requestId:'r2'}],['library_scan',{rebuild:true}],['library_cancel_scan',undefined],['close_record',{recordId:'handle'}],
    ]);
  });
});
