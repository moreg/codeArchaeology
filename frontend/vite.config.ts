import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  // 默认根路径部署；GitHub Pages 通过环境变量 GITHUB_PAGES=true 切到子路径
  // 设置 GITHUB_PAGES_BASE 可自定义仓库名（默认 /codeArchaeology/）
  base: process.env.GITHUB_PAGES
    ? (process.env.GITHUB_PAGES_BASE || '/codeArchaeology/')
    : '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          'cytoscape-vendor': ['cytoscape', 'cytoscape-cose-bilkent'],
          'monaco-vendor': ['monaco-editor', '@monaco-editor/react'],
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
          'react-vendor': ['react', 'react-dom'],
        },
      },
    },
  },
});
