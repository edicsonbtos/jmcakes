import type { Metadata } from "next";
import { notFound } from "next/navigation";

export const metadata: Metadata = { title: "Sistema de diseño", robots: { index: false, follow: false } };

/** Se lee en cada petición: un build de producción solo la muestra con ENABLE_DESIGN_PAGE=1 (CI de capturas). */
export const dynamic = "force-dynamic";

/** `/design` existe solo en desarrollo (DSN): tokens, componentes y pantallas de muestra con datos de ejemplo. */
export default function DesignLayout({ children }: { children: React.ReactNode }) {
  if (process.env.NODE_ENV === "production" && process.env.ENABLE_DESIGN_PAGE !== "1") notFound();
  return children;
}
