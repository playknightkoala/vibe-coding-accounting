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
