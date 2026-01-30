import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/DeepRecall/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  build: {
    sourcemap: false, // Security: Hide source code filenames in production
    chunkSizeWarningLimit: 1000,
  },
});
