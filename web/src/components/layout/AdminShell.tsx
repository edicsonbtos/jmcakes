import { type ReactNode } from "react";
import { Sidebar, type RateSummary } from "./Sidebar";

/**
 * Armazón del panel: riel en escritorio, barras en el teléfono y el contenido centrado.
 * `(admin)/layout.tsx` le pasa el nombre del negocio (`/settings/public`) y la tasa de hoy.
 */
export function AdminShell({
  businessName,
  rate,
  activePath,
  children,
}: {
  businessName: string;
  rate: RateSummary;
  /** Solo para /design: fija la sección activa. */
  activePath?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas lg:flex-row">
      <Sidebar businessName={businessName} rate={rate} activePath={activePath} />
      <main id="contenido" className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-[72rem] px-4 pb-10 pt-5 md:px-8 md:pt-8 lg:px-10">{children}</div>
      </main>
    </div>
  );
}
