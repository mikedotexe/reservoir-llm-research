import { configDefaults, defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  // Preserved qualification source is evidence, not part of the current test suite.
  test: { exclude: [...configDefaults.exclude, 'target/**'] },
  server: { host: '127.0.0.1', port: 1420, strictPort: true },
  build: { target: ['es2022', 'safari16'], sourcemap: true },
});
