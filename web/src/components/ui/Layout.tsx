// Adaptado de OpenGravity: apps/web/src/components/{page-title,data-section}.tsx
import Link from "next/link";
import { type ReactNode } from "react";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";

/** Encabezado de página: título pesado, una línea de contexto y las acciones a la derecha. */
export function PageHeader({
  title,
  description,
  actions,
  back,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  /** Enlace "volver" (en el teléfono es la única navegación de las subpáginas). */
  back?: { href: string; label: string };
  className?: string;
}) {
  return (
    <header className={cn("flex flex-col gap-3", className)}>
      {back ? (
        <Link
          href={back.href}
          className="-ml-3 inline-flex h-12 w-fit items-center gap-1 rounded-pill pl-2 pr-4 text-base font-semibold text-ink hover:bg-canvas-subtle"
        >
          <ChevronLeft aria-hidden className="size-6" />
          {back.label}
        </Link>
      ) : null}
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-heavy text-ink md:text-3xl">{title}</h1>
          {description ? <p className="mt-1 text-base text-ink-muted">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}

/** Sección con título de bloque (sin tarjeta alrededor: el espacio separa). */
export function Section({
  title,
  actions,
  children,
  className,
  id,
}: {
  title: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section aria-labelledby={id} className={cn("flex flex-col gap-2", className)}>
      <div className="flex min-h-12 items-center justify-between gap-3">
        <h2 id={id} className="text-xl font-heavy text-ink">
          {title}
        </h2>
        {actions}
      </div>
      {children}
    </section>
  );
}

/**
 * Barra de acciones al alcance del pulgar: fija abajo en el teléfono (con el área segura)
 * y en línea desde 768 px. Úsala para las dos acciones de la ficha.
 */
export function ActionBar({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <>
      {/* Reserva el alto de la barra para que el final de la lista no quede debajo. */}
      <div aria-hidden className="h-24 md:hidden" />
      <div
        className={cn(
          "fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]",
          "md:static md:z-auto md:border-0 md:bg-transparent md:p-0",
          className,
        )}
      >
        <div className="mx-auto grid max-w-3xl grid-cols-2 gap-3">{children}</div>
      </div>
    </>
  );
}
