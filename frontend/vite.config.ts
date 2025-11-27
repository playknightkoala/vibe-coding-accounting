import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    build: {
      // Enable minification
      minify: 'esbuild',
      // Target modern browsers for smaller bundle
      target: 'es2015',
      // Enable CSS code splitting
      cssCodeSplit: true,
      // Rollup options for chunk optimization
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'chart-vendor': ['chart.js'],
            'utils': ['axios']
          },
          // Asset file naming with hash for cache busting
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return `assets/images/[name]-[hash][extname]`
            } else if (/woff2?|ttf|otf|eot/i.test(ext)) {
              return `assets/fonts/[name]-[hash][extname]`
            }
            return `assets/[name]-[hash][extname]`
          },
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js'
        }
      },
      // Source maps for production debugging (optional)
      sourcemap: false,
      // Chunk size warnings
      chunkSizeWarningLimit: 1000
    },
    server: {
      port: 5173,
      host: true,
      allowedHosts: env.VITE_ALLOWED_HOSTS
        ? env.VITE_ALLOWED_HOSTS.split(',').map((host: string) => host.trim())
        : ['localhost', '127.0.0.1'],
      hmr: env.VITE_HMR_CLIENT_PORT === 'false' ? false : {
        // Configure HMR for production if needed
        clientPort: env.VITE_HMR_CLIENT_PORT ? parseInt(env.VITE_HMR_CLIENT_PORT) : undefined,
        host: env.VITE_HMR_HOST || undefined,
        protocol: env.VITE_HMR_PROTOCOL || undefined
      }
    }
  }
})
