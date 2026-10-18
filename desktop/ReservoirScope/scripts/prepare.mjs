import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const interpreter = process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3');
for (const name of ['stage_resources.py', 'stage_activation_bootstrap.py']) {
  const script = fileURLToPath(new URL(`./${name}`, import.meta.url));
  const result = spawnSync(interpreter, [script], { stdio: 'inherit' });
  if (result.error) {
    console.error(`Resource staging needs Python 3.12+: ${result.error.message}`);
  }
  if (result.status !== 0) process.exit(result.status ?? 1);
}
