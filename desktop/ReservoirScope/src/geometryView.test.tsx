import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import GeometryWorkspace, { GeometryAccount, GeometryCapture, GeometryProvenance, geometryUtc } from './GeometryWorkspace';
import { GeometryController } from './geometryController';
import { geometryFixture } from './geometryFixtures.test-support';

describe('geometry evidence presentation', () => {
  it('renders 128 exact signed coordinates, original clocks and explicit gaps', () => {
    const snapshot = geometryFixture().records[0].snapshot!;
    const html = renderToStaticMarkup(createElement(GeometryCapture, { snapshot, frameIndex: 2, coordinate: 127, expanded: true, onSeek: () => {}, onCoordinate: () => {}, onExpand: () => {} }));
    expect((html.match(/Select geometry coordinate /g) ?? []).length).toBe(128);
    expect(html).toContain('11000…13000'); expect(html).toContain('1790000013000');
    expect(html).toContain('original signed coordinates'); expect(html).toContain('No PCA, interpolation or inferred eigenvectors');
    expect(html).not.toContain('fillPercent'); expect(html).not.toContain('src="minime/');
    expect(html).toContain('minime/workspace/runtime/esn_activation_trace_v1.json');
  });
  it('distinguishes authored text from computed comparison and escapes markup', () => {
    const packet = geometryFixture();
    const comparison = renderToStaticMarkup(createElement(GeometryAccount, { entry: packet.records[3] }));
    expect(comparison).not.toContain('Authored account');
    const capture = renderToStaticMarkup(createElement(GeometryAccount, { entry: { ...packet.records[0], authoredText: '<script>untrusted instruction</script>' } }));
    expect(capture).toContain('&lt;script&gt;untrusted instruction&lt;/script&gt;'); expect(capture).not.toContain('<script>');
  });
  it('retains the reading through hidden view and distinguishes explicit file origin', async () => {
    const controller = new GeometryController({ open: async requestId => ({ requestId, cancelled: false, packet: geometryFixture('openedFile') }), export: async (requestId, packetId) => ({ requestId, packetId, file: null }) });
    await controller.open(); controller.select(2); controller.seek(2); controller.expand(true);
    expect(renderToStaticMarkup(createElement(GeometryWorkspace, { active: false, controller }))).toBe('');
    const html = renderToStaticMarkup(createElement(GeometryWorkspace, { active: true, controller }));
    expect(html).toContain('Recorded frame 3 / 3'); expect(html).not.toContain('Synthetic example · invented coordinates and text');
    expect(controller.snapshot().selected).toBe(2); expect(controller.snapshot().coordinatesExpanded).toBe(true);
  });
  it('exposes authored limits and separates body/file identities from authenticity', () => {
    const packet = geometryFixture(); const html = renderToStaticMarkup(createElement(GeometryProvenance, { packet }));
    expect(html).toContain(packet.sha256); expect(html).toContain(packet.bodySha256); expect(html).toContain(packet.limits);
    expect(html).toContain('producer authenticity and historical novelty are not established');
  });
  it('does not round u64 clocks into invented dates', () => {
    expect(geometryUtc('18446744073709551615')).toContain('Outside the calendar display range');
    expect(geometryUtc('0')).toBe('1970-01-01T00:00:00.000Z');
  });
});
