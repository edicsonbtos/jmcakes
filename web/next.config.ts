// Adaptado de OpenGravity: apps/web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // El build de producción no type-chequea las pruebas: importan devDependencies.
  // `tsc --noEmit` (tsconfig.json) sigue cubriéndolas en local y en CI.
  typescript: { tsconfigPath: "tsconfig.build.json" },
  poweredByHeader: false,
  // Playwright y los agentes abren `next dev` por 127.0.0.1 (docs/plan/05 §1).
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  // Sin el indicador flotante de desarrollo: tapa la barra de acciones en las capturas.
  devIndicators: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
