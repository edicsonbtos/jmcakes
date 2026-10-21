// Adaptado de OpenGravity: apps/web/src/components/layout/Sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { CircleDollarSign, Croissant, House, LogOut, Menu, ScrollText, Settings, Users, type LucideIcon } from "lucide-react";
import { Sheet } from "@/components/ui/Sheet";
import { cn } from "@/lib/utils";
import { BrandMark } from "./BrandMark";

export type NavItem = { href: string; label: string; icon: LucideIcon; primary: boolean };

/** Navegación de E1 (09 §E1 — Pantallas). Solo existe lo que está en la etapa. */
export const NAV_ITEMS: readonly NavItem[] = [
  { href: "/admin", label: "Inicio", icon: House, primary: true },
  { href: "/admin/clientes", label: "Clientes", icon: Users, primary: true },
  { href: "/admin/productos", label: "Productos", icon: Croissant, primary: true },
  { href: "/admin/tasa", label: "Tasa", icon: CircleDollarSign, primary: false },
  { href: "/admin/configuracion", label: "Configuración", icon: Settings, primary: false },
  { href: "/admin/auditoria", label: "Auditoría", icon: ScrollText, primary: false },
];

export function isActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Las subpáginas (ficha, importar) esconden la barra inferior: allí manda su propia barra de acciones. */
export function isTopLevel(pathname: string): boolean {
  return NAV_ITEMS.some((i) => i.href === pathname);
}

export type RateSummary = { label: string; value: string } | null;

function LogoutButton({ className }: { className?: string }) {
  return (
    <form method="post" action="/api/auth/logout" className={className}>
      <button
        type="submit"
        className="flex h-12 w-full items-center gap-3 rounded-md px-3 text-base font-semibold text-ink-muted transition-colors duration-150 hover:bg-canvas-subtle hover:text-ink"
      >
        <LogOut aria-hidden className="size-5" strokeWidth={2.25} />
        Cerrar sesión
      </button>
    </form>
  );
}

function RateLine({ rate }: { rate: RateSummary }) {
  return (
    <div className="px-3 py-2">
      <p className="text-sm text-ink-muted">{rate ? rate.label : "Tasa del día"}</p>
      <p className="text-base font-bold tnum text-ink">{rate ? rate.value : "Sin tasa"}</p>
    </div>
  );
}

/**
 * Escritorio (≥1024 px): riel izquierdo con marca, secciones, tasa y salida.
 * Teléfono: barra superior con la marca y la tasa, y barra inferior con Inicio, Clientes,
 * Productos y "Más" (hoja con el resto y "Cerrar sesión").
 */
export function Sidebar({ businessName, rate, activePath }: { businessName: string; rate: RateSummary; activePath?: string }) {
  const current = usePathname();
  const pathname = activePath ?? current ?? "";
  const [moreOpen, setMoreOpen] = useState(false);
  const secondaryActive = NAV_ITEMS.some((i) => !i.primary && isActive(pathname, i.href));

  return (
    <>
      {/* Escritorio */}
      <aside className="sticky top-0 hidden h-dvh w-[var(--size-sidebar)] shrink-0 flex-col border-r border-line bg-canvas px-3 py-5 lg:flex">
        <Link href="/admin" className="mx-1 block min-w-0 rounded-md px-2 py-1" aria-label={`${businessName}: inicio`}>
          <BrandMark name={businessName} />
        </Link>
        <nav aria-label="Secciones" className="mt-8 flex flex-col gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex h-12 items-center gap-3 rounded-md px-3 text-base transition-colors duration-150",
                  active ? "bg-canvas-subtle font-bold text-ink" : "font-medium text-ink-muted hover:bg-canvas-subtle hover:text-ink",
                )}
              >
                <Icon aria-hidden className={cn("size-5", active && "text-brand")} strokeWidth={active ? 2.5 : 2} />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto flex flex-col gap-2 border-t border-line pt-4">
          <RateLine rate={rate} />
          <LogoutButton />
        </div>
      </aside>

      {/* Teléfono y tablet: barra superior */}
      <header className="sticky top-0 z-20 flex h-[var(--size-topbar)] items-center justify-between gap-3 border-b border-line bg-canvas px-4 pt-[env(safe-area-inset-top)] lg:hidden">
        <Link href="/admin" className="min-w-0" aria-label={`${businessName}: inicio`}>
          <BrandMark name={businessName} compact />
        </Link>
        <span
          className="shrink-0 rounded-pill bg-canvas-subtle px-3 py-1.5 text-sm font-semibold tnum text-ink"
          title={rate?.label}
        >
          {rate ? `Tasa ${rate.value}` : "Sin tasa"}
        </span>
      </header>

      {/* Teléfono y tablet: barra inferior, solo en las páginas principales */}
      {isTopLevel(pathname) ? (
        <>
          <nav
            aria-label="Secciones"
            className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t border-line bg-canvas pb-[env(safe-area-inset-bottom)] lg:hidden"
          >
            {NAV_ITEMS.filter((i) => i.primary).map(({ href, label, icon: Icon }) => {
              const active = isActive(pathname, href);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn("flex h-16 flex-col items-center justify-center gap-1 text-xs", active ? "font-bold text-ink" : "font-medium text-ink-muted")}
                >
                  <Icon aria-hidden className={cn("size-6", active && "text-brand")} strokeWidth={active ? 2.5 : 2} />
                  {label}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={() => setMoreOpen(true)}
              aria-haspopup="dialog"
              className={cn("flex h-16 flex-col items-center justify-center gap-1 text-xs", secondaryActive ? "font-bold text-ink" : "font-medium text-ink-muted")}
            >
              <Menu aria-hidden className={cn("size-6", secondaryActive && "text-brand")} strokeWidth={secondaryActive ? 2.5 : 2} />
              Más
            </button>
          </nav>
          <div aria-hidden className="h-20 lg:hidden" />
        </>
      ) : null}

      <Sheet open={moreOpen} onClose={() => setMoreOpen(false)} title="Más">
        <nav aria-label="Más secciones" className="-mx-2 flex flex-col">
          {NAV_ITEMS.filter((i) => !i.primary).map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMoreOpen(false)}
              aria-current={isActive(pathname, href) ? "page" : undefined}
              className="flex h-14 items-center gap-3 rounded-md px-2 text-base font-semibold text-ink hover:bg-canvas-subtle"
            >
              <span className="inline-flex size-10 items-center justify-center rounded-pill bg-canvas-subtle">
                <Icon aria-hidden className="size-5" />
              </span>
              {label}
            </Link>
          ))}
        </nav>
        <div className="-mx-2 mt-3 border-t border-line pt-3">
          <RateLine rate={rate} />
          <LogoutButton />
        </div>
      </Sheet>
    </>
  );
}
