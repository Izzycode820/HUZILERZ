import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  define: {
    // Replace process.env.NODE_ENV at build time for browser compatibility
    // React uses this to enable/disable development features
    'process.env.NODE_ENV': JSON.stringify('production')
  },
  build: {
    lib: {
      entry: resolve(__dirname, 'entry.mjs'),
      formats: ['es'],
      fileName: 'entry'
    },
    rollupOptions: {
      external: [],
      output: {
        preserveModules: false,
        inlineDynamicImports: true
      }
    },
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true
  }
})
