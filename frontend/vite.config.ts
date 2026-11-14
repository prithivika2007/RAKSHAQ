import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'import.meta.env.VITE_DASHBOARD_URL': JSON.stringify(env.VITE_DASHBOARD_URL || '')
    },
    server: {
      port: 5174,
      host: '0.0.0.0',
      strictPort: true
    }
  };
});