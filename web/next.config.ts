// Adaptado de OpenGravity: apps/web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // El build de producción no type-chequea las pruebas: importan devDependencies.
  // `tsc --noEmit` (tsconfig.json) sigue cubriéndolas en local y en CI.
  typescript: { tsconfigPath: "tsconfig.build.json" },
  poweredByHeader: false,
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
