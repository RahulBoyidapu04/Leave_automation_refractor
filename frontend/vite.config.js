
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/me': 'http://localhost:8000',
      '/apply-leave': 'http://localhost:8000',
      '/availability': 'http://localhost:8000',
      '/manager': 'http://localhost:8000',
      '/leave': 'http://localhost:8000',
      '/notifications': 'http://localhost:8000',
      '/auth': 'http://localhost:8000'
    }
  },
  build: {
    outDir: 'dist',
  }
});
