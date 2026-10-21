// Adaptado de OpenGravity: apps/web/vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    // TZ=UTC a propósito: si un formateador pierde timeZone "America/Caracas",
    // la prueba falla en vez de pasar por casualidad del reloj de la máquina.
    env: {
      TZ: "UTC",
      JWT_SECRET: "dev-mock-secret-no-usar-en-prod",
      NEXT_PUBLIC_API_URL: "http://api.test/api/v1",
    },
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
