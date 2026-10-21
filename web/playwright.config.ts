import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import path from "node:path";

/**
 * Playwright del panel (01: corre en GitHub Actions; en el contenedor solo si hay Chromium
 * preinstalado). Puertos por agente (docs/plan/05 §1): WEB_PORT y MOCK_PORT.
 * - Prism sirve `contracts/openapi.json` si existe (lo genera FND y lo publica el orquestador en G1).
 * - En CI se usa `next start` sobre el build; en local, `next dev`.
 */
const WEB_PORT = Number(process.env.WEB_PORT ?? 3000);
const MOCK_PORT = Number(process.env.MOCK_PORT ?? 4010);
const CONTRACT = path.resolve(__dirname, "../contracts/openapi.json");
const BASE_URL = `http://127.0.0.1:${WEB_PORT}`;

const webEnv = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? `http://127.0.0.1:${MOCK_PORT}/api/v1`,
  JWT_SECRET: process.env.JWT_SECRET ?? "dev-mock-secret-no-usar-en-prod",
  ENABLE_DESIGN_PAGE: "1",
};

const servers = [];
if (existsSync(CONTRACT) && !process.env.PW_NO_MOCK) {
  servers.push({
    command: `npx prism mock --host 127.0.0.1 --port ${MOCK_PORT} "${CONTRACT}"`,
    url: `http://127.0.0.1:${MOCK_PORT}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  });
}
servers.push({
  command: process.env.CI ? `npx next start --port ${WEB_PORT}` : `npx next dev --port ${WEB_PORT}`,
  url: `${BASE_URL}/login`,
  env: webEnv,
  reuseExistingServer: !process.env.CI,
  timeout: 180_000,
});

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    locale: "es-VE",
    timezoneId: "America/Caracas",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { browserName: "chromium", viewport: { width: 1440, height: 900 } } },
    {
      name: "mobile",
      use: { browserName: "chromium", viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
    },
  ],
  webServer: servers,
});
