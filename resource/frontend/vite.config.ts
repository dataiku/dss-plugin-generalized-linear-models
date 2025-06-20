import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from "@quasar/vite-plugin";


// https://vitejs.dev/config/
const config = defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls },
    }),
    quasar({
    })
  ],
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "quasar/src/css/index.sass" as *;`,
        quietDeps: true,
        silenceDeprecations: ['legacy-js-api', 'slash-div']

      },
      sass: {
        quietDeps: true,
        silenceDeprecations: ['legacy-js-api', 'slash-div']
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    dedupe: ['vue']
  },
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        secure: false,
        //rewrite: (path) => path.replace(/^\/api/, ""),
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
  base: process.env.MODE === 'production' ? "/plugins/generalized-linear-models/resource/dist/" : "/"
});


export default config;
