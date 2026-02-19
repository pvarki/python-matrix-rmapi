import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { federation } from "@module-federation/vite";
import path from "path";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const isProd = mode === "production";

  return {
    server: {
      fs: {
        allow: [".", "../shared"],
      },
      proxy: {
        "/ui/matrix": {
          target: "http://localhost:4174",
          rewrite: (path) => path.replace(/^\/ui\/matrix/, ""),
        },
      },
    },
    build: {
      target: "chrome89",
      emptyOutDir: true,
      rollupOptions: {
        preserveEntrySignatures: "exports-only",
      },
    },
    plugins: [
      federation({
        filename: "remoteEntry.js",
        name: "matrix-integration",
        exposes: {
          "./remote-ui": "./src/App.tsx",
        },
        remotes: {},
        shared: {
          react: {
            requiredVersion: "18.3.1",
            singleton: true,
          },
          i18next: {
            requiredVersion: "25.6.2",
            singleton: true,
          },
          "react-i18next": {
            requiredVersion: "16.3.3",
            singleton: true,
          },
          "@tanstack/react-router": {
            requiredVersion: "1.135.2",
            singleton: true,
          },
        },
        runtime: "@module-federation/enhanced/runtime",
      }),
      react(),
      tailwindcss(),
    ],
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
    define: {
      __USE_GLOBAL_CSS__: JSON.stringify(
        process.env.VITE_USE_GLOBAL_CSS === "true",
      ),
    },
  };
});
