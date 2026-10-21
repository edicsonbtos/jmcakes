// Adaptado de OpenGravity: apps/web/eslint.config.mjs
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // El dinero viaja como string decimal: nunca parseFloat sobre montos (ver lib/money.ts).
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='parseFloat']",
          message: "No uses parseFloat: el dinero es string decimal (lib/money.ts).",
        },
      ],
      "no-console": ["error", { allow: ["error"] }],
    },
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "playwright-report/**",
    "test-results/**",
    "src/lib/api-types.ts",
  ]),
]);
