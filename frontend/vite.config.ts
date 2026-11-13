import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const defaultDashboardUrl = 'http://127.0.0.1:5173/index.html?mode=preview';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'import.meta.env.VITE_DASHBOARD_URL': JSON.stringify(
        env.VITE_DASHBOARD_URL || defaultDashboardUrl
      )
    },
    server: {
      port: 5174,
      host: '127.0.0.1',
      strictPort: true
    }
  };
});