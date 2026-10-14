import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const interpreter = process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3');
const script = fileURLToPath(new URL('./stage_resources.py', import.meta.url));
const result = spawnSync(interpreter, [script], { stdio: 'inherit' });
if (result.error) {
  console.error(`Resource staging needs Python 3.12+: ${result.error.message}`);
}
process.exit(result.status ?? 1);
