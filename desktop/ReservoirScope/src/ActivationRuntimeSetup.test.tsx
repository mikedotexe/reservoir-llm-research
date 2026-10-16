import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import ActivationRuntimeSetup, { setupBytes } from './ActivationRuntimeSetup';
import { ActivationSetupController } from './activationSetupController';
import type { ActivationSetupApi, ActivationSetupStatus } from './activationSetupTypes';

const missing: ActivationSetupStatus = { state: 'missing', phase: 'check', message: 'No owned installation is ready.', canResume: false, totalBytes: 2.5 * 1024 ** 3, requiredBytes: 8 * 1024 ** 3 };
async function fixture(status?: ActivationSetupStatus) {
  const api: ActivationSetupApi = { status: vi.fn(async () => status ?? missing), prepare: vi.fn(async () => missing), cancel: vi.fn(async () => missing) };
  const controller = new ActivationSetupController(api);
  if (status) await controller.refresh();
  return { controller, api };
}

describe('Activation runtime preparation interface', () => {
  it('opening the component alone dispatches no installation or model work', async () => {
    const { controller, api } = await fixture();
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(api.prepare).not.toHaveBeenCalled(); expect(api.cancel).not.toHaveBeenCalled();
    expect(html).toContain('Downloads begin only when you choose Prepare');
    expect(html).toContain('Create and Start follow separately');
    expect(html).toContain('Read examples immediately'); expect(html).toContain('No Terminal is needed');
    expect(html).toContain('aria-live="polite"'); expect(html).toContain('Check setup status');
  });

  it('shows required platform, reported download/storage sizes and optional local evidence', async () => {
    const { controller } = await fixture(missing);
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(html).toContain('Apple Silicon and macOS 26 or later'); expect(html).toContain('tested on macOS 27.0.1');
    expect(html).toContain('2.50 GiB'); expect(html).toContain('8.00 GiB');
    expect(html).toContain('Local setup evidence'); expect(html).toContain('does not establish that a model request will finish');
    expect(html).toMatch(/<button class="primary-button">Prepare activation runtime<\/button>/);
    expect(html).not.toContain('Resume preparation</button>');
  });

  it('uses only reported progress and provides cancellation while an experiment busy flag is set', async () => {
    const { controller } = await fixture({ ...missing, state: 'preparing', phase: 'verify_assets', message: 'Verifying downloaded assets.', downloadedBytes: 2048, totalBytes: 4096 });
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller} busy/>);
    expect(html).toContain('Current phase: verify assets'); expect(html).toContain('2.0 KiB received of 4.0 KiB');
    expect(html).toContain('value="2048" max="4096"'); expect(html).toContain('aria-label="Current preparation phase progress"');
    expect(html).toMatch(/<button>Cancel preparation<\/button>/); expect(html).toContain('30-minute deadline');
    expect(html).not.toContain('Resume preparation</button>');
  });

  it('keeps unknown download totals indeterminate instead of inventing a percentage', async () => {
    const { controller } = await fixture({ ...missing, state: 'preparing', phase: 'dependencies', totalBytes: null, downloadedBytes: null, requiredBytes: null });
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(html).toMatch(/<progress[^>]+><\/progress>/); expect(html).not.toContain('max="'); expect(html).not.toContain('value="');
    expect(html.match(/Not yet reported/g)).toHaveLength(2);
  });

  it('offers only an explicit resume for a recognized interrupted preparation', async () => {
    const { controller } = await fixture({ ...missing, state: 'interrupted', canResume: true, message: 'Preparation was stopped.' });
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(html).toContain('Resume preparation</button>'); expect(html).not.toContain('>Prepare activation runtime</button>');
    expect(html).toContain('Preparation remains paused until you choose Resume preparation');
    expect(renderToStaticMarkup(<ActivationRuntimeSetup controller={controller} busy/>)).toMatch(/<button class="primary-button" disabled="">Resume preparation<\/button>/);
  });

  it('preserves actionable failure text as inert text and requires status read after command error', async () => {
    const { controller, api } = await fixture(missing);
    vi.mocked(api.prepare).mockRejectedValueOnce(new Error('Storage check failed: <script>inert</script>')); await controller.prepare();
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(html).toContain('role="alert"'); expect(html).toContain('&lt;script&gt;inert&lt;/script&gt;'); expect(html).not.toContain('<script>');
    expect(html).toContain('Check setup status before trying again'); expect(html).toMatch(/<button class="primary-button" disabled="">Prepare activation runtime<\/button>/);
    expect(html).toMatch(/<button>Check setup status<\/button>/);
  });

  it('leaves examples available on unsupported computers and does not offer preparation', async () => {
    const { controller } = await fixture({ ...missing, state: 'unsupported', message: 'This is not an Apple Silicon Mac.' });
    const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller}/>);
    expect(html).toContain('The offline examples remain available'); expect(html).not.toContain('>Prepare activation runtime</button>');
    expect(html).not.toContain('Resume preparation</button>'); expect(html).not.toContain('Cancel preparation</button>');
  });

  it('keeps readiness separate from Start and renders local paths only in collapsed evidence', async () => {
    const { controller } = await fixture({ ...missing, state: 'ready', pythonPath: '/Local Path/python', modelPath: '/Local Path/model', message: 'Verified.' });
    const onReady = vi.fn(); const html = renderToStaticMarkup(<ActivationRuntimeSetup controller={controller} onReady={onReady}/>);
    expect(html).toContain('Activation runtime ready'); expect(html).toContain('Check the experiment settings below');
    expect(html).toContain('Start performs a separate memory check'); expect(html).not.toContain('>Prepare activation runtime</button>');
    expect(html).toContain('<details class="activation-runtime-evidence">'); expect(html).toContain('/Local Path/python');
    expect(onReady).not.toHaveBeenCalled();
  });

  it('formats bytes without labeling binary quantities as decimal gigabytes', () => {
    expect(setupBytes(0)).toBe('0 bytes'); expect(setupBytes(100)).toBe('100 bytes');
    expect(setupBytes(1024)).toBe('1.0 KiB'); expect(setupBytes(1024 ** 2)).toBe('1.0 MiB'); expect(setupBytes(1024 ** 3)).toBe('1.00 GiB');
  });
});
