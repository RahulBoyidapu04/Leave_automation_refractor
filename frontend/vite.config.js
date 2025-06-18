
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api/v1/leave': 'http://localhost:8001', // <-- Add this line
      '/me': 'http://localhost:8001',
      '/apply-leave': 'http://localhost:8001',
      '/availability': 'http://localhost:8001',
      '/manager': 'http://localhost:8001',
      '/leave': 'http://localhost:8001',
      '/notifications': 'http://localhost:8001',
      '/auth': 'http://localhost:8001'
    }
  },
  build: {
    outDir: 'dist',
  }
});
