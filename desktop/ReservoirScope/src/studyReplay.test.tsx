import { existsSync, readFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import StudyWalkthrough from './StudyWalkthrough';
import { conditions, matchesReport, recalculate, reported, rules, scoreRow, type SavedStudy } from './studyReplay';

// Synthetic, deliberately simple test data. This is never displayed as S-021 evidence.
function fixture(): SavedStudy {
  const study: SavedStudy = {schemaVersion:1,study:'S-021',source:{closedSha256:'test',scoreSha256:'test',designSha256:'test',model:'test',modelDigest:'test',providerVersion:'test',temperature:0,contextTokens:1},worlds:[],prompts:{},rows:[]};
  for (let base=0;base<6;base++) {
    study.worlds.push({base,subject:`Test ${base}`,x:24,oldThreshold:50,changedThreshold:19});
    for (const rule of rules) for (const condition of conditions) for (const seed of [7,20260909]) {
      const threshold = rule === 'changed' ? 19 : 50;
      const relation = rule === 'changed' ? 'GE' : 'LT';
      const prefix = `{"x":24,"current_threshold":${threshold},"relation":`;
      const action = rule === 'changed' ? 'ROUTE_HIGH' : 'ROUTE_LOW';
      study.rows.push({id:`s021-study-base-${String(base).padStart(2,'0')}-${rule}-${condition}-s${seed}`,base,rule,condition,seed,status:'complete',
        prefix:condition === 'operands_only' ? prefix : `${prefix}"${condition === 'flipped' ? (relation === 'GE' ? 'LT' : 'GE') : relation}","action":`,
        suffix:condition === 'operands_only' ? `"${relation}","action":"${action}","account":"Test account."}` : `"${action}","account":"Test account."}`,
        requestSha256:'test',responseSha256:'test'});
    }
  }
  return study;
}

describe('saved S-021 action replay', () => {
  it('reads actions from raw continuations and derives costs from world facts', () => {
    const study = fixture();
    expect(recalculate(study).groups.every(g => g.correct === 12 && g.cost === 0)).toBe(true);
    const row = study.rows.find(r => r.rule === 'changed' && r.condition === 'flipped')!;
    row.suffix = '"ROUTE_LOW","account":"Wrong route, despite the facts."}';
    const wrong = recalculate(study);
    expect(wrong.groups.find(g => g.rule === 'changed' && g.condition === 'flipped')).toMatchObject({n:12,correct:11,wrong:1,measure:0,cost:4});
    expect(wrong.pairedGain).toBe(4/12);
    row.suffix = '"MEASURE","account":"Measure instead."}';
    expect(scoreRow(study,row)).toMatchObject({correct:false,measure:true,cost:1});
    expect(recalculate(study).pairedGain).toBe(1/12);
    expect(matchesReport(wrong)).toBe(false);
  });
  it('rejects missing, duplicate and mislabeled trials instead of dropping them', () => {
    const missing = fixture(); missing.rows.pop(); expect(() => recalculate(missing)).toThrow('72');
    const duplicate = fixture(); duplicate.rows[1] = duplicate.rows[0]; expect(() => recalculate(duplicate)).toThrow('Duplicate');
    const mislabeled = fixture(); mislabeled.rows[0].id = 'other'; expect(() => recalculate(mislabeled)).toThrow('unexpected');
    const incomplete = fixture(); incomplete.rows[0].status = 'incomplete'; expect(() => recalculate(incomplete)).toThrow('incomplete');
  });
  it('rejects altered prefixes, malformed JSON and duplicate response keys', () => {
    const study = fixture(); const row = study.rows.find(r => r.condition === 'correct')!;
    const original = row.prefix;
    row.prefix = row.prefix.replace('24','25'); expect(() => scoreRow(study,row)).toThrow('prefix'); row.prefix = original;
    for (const suffix of ['"ROUTE_HIGH","account":"One","action":"MEASURE"}', '"ROUTE_HIGH","account":"One",}', '"ROUTE_HIGH","account":{}}', '"ROUTE_HIGH","account":""}', '"ROUTE_HIGH","account":"One"} trailing']) {
      row.suffix = suffix; expect(() => scoreRow(study,row)).toThrow();
    }
    row.suffix = '"ROUTE_HIGH","account":"Quoted \\"action\\": and comma, within text."}'.replaceAll('\\\\"','\\"');
    expect(scoreRow(study,row).action).toBe('ROUTE_HIGH');
  });
  it('uses the HIGH route at equality', () => {
    const study = fixture(); study.worlds[0].x = 19;
    const row = study.rows.find(r => r.condition === 'correct')!; row.prefix = row.prefix.replace('24','19');
    expect(scoreRow(study,row)).toMatchObject({correct:true,cost:0});
  });
  it('compares every group and the paired contrast with the separate reported values', () => {
    expect(matchesReport(structuredClone(reported))).toBe(true);
    const changed = structuredClone(reported); changed.groups[0].wrong++; expect(matchesReport(changed)).toBe(false);
  });
  it('states absent private data clearly without offering a nonworking recalculation button', () => {
    const html = renderToStaticMarkup(createElement(StudyWalkthrough,{active:true,study:null}));
    expect(html).toContain('not included in this build');
    expect(html).not.toContain('class="primary-button"');
    expect(html.indexOf('01 / Question')).toBeLessThan(html.indexOf('02 / Result'));
    expect(html.indexOf('03 / One example')).toBeLessThan(html.indexOf('04 / Recalculate'));
  });
  it('keeps the reported finding readable when a packet has an invalid shape', () => {
    for (const study of [{}, [], 'bad data', {...fixture(),source:null}]) {
      const html = renderToStaticMarkup(createElement(StudyWalkthrough,{active:true,study}));
      expect(html).toContain('saved study packet is invalid');
      expect(html).not.toContain('class="primary-button"');
    }
  });
});

const privatePath = new URL('./local-studies/s021.json', import.meta.url);
it.skipIf(!existsSync(privatePath))('reconstructs every reported group and the selected example from the staged private evidence', () => {
  const study = JSON.parse(readFileSync(privatePath,'utf8')) as SavedStudy;
  const actual = recalculate(study);
  expect(actual).toEqual(reported);
  expect(matchesReport(actual)).toBe(true);
  const pair = study.rows.filter(r => r.base === 0 && r.rule === 'changed' && r.seed === 7 && r.condition !== 'operands_only').map(r => scoreRow(study,r));
  expect(pair.map(r => [r.action,r.cost])).toEqual([['ROUTE_HIGH',0],['MEASURE',1]]);
  const html = renderToStaticMarkup(createElement(StudyWalkthrough,{active:true,study}));
  expect(html).toContain('Its x is fixed from that snapshot onward');
  expect(html).toContain('the only warranted action is to MEASURE');
});
