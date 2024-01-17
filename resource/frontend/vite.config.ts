import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from "@quasar/vite-plugin";



// https://vitejs.dev/config/
const config = defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls },
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      }
    }
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name].js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name].[ext]`
      }
    },
    watch: {
      exclude: "node_modules/**"
    }
  },
  base: process.env.MODE === 'production' ? "/plugins/document-question-answering/resource/dist/" : "/"
});


export default config;
