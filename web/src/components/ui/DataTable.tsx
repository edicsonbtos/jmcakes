// Adaptado de OpenGravity: apps/web/src/components/ui/DataTable.tsx
"use client";

import { type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { Skeleton } from "./Skeleton";

export type DataTableColumn<T> = {
  key: string;
  header: ReactNode;
  render: (row: T, index: number) => ReactNode;
  /** Montos y cantidades a la derecha. */
  align?: "start" | "end";
  className?: string;
  /** Oculta la columna bajo 1024 px. */
  hideBelowLg?: boolean;
};

export type DataTableProps<T> = {
  columns: ReadonlyArray<DataTableColumn<T>>;
  rows: ReadonlyArray<T>;
  rowKey: (row: T, index: number) => string;
  /** Leyenda de la tabla para lectores de pantalla. */
  caption: string;
  loading?: boolean;
  /** Lo que se ve cuando no hay filas (con su acción). */
  empty?: ReactNode;
  /** Navega al tocar la fila. */
  rowHref?: (row: T) => string;
  onRowClick?: (row: T) => void;
  /** Bajo 768 px se dibuja esta fila en lugar de la tabla (lista de app). */
  mobileRender?: (row: T, index: number) => ReactNode;
  /** Paginación por cursor (08: `{items, nextCursor}`): hay más si no es null. */
  nextCursor?: string | null;
  onLoadMore?: (cursor: string) => void;
  loadingMore?: boolean;
  className?: string;
};

/**
 * Tabla para catálogos y registros (productos, tasa, auditoría). Filtros, orden y
 * paginación los resuelve el servidor; aquí solo se dibuja y se pide la página siguiente.
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  loading = false,
  empty,
  rowHref,
  onRowClick,
  mobileRender,
  nextCursor = null,
  onLoadMore,
  loadingMore = false,
  className,
}: DataTableProps<T>) {
  const router = useRouter();
  const clickable = !!rowHref || !!onRowClick;
  const activate = (row: T) => {
    if (onRowClick) onRowClick(row);
    else if (rowHref) router.push(rowHref(row));
  };

  if (loading) {
    return (
      <div role="status" aria-label="Cargando…" className={cn("flex flex-col gap-3 py-2", className)}>
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (rows.length === 0) {
    return <div className={className}>{empty ?? <EmptyState title="No hay nada que mostrar con estos filtros." />}</div>;
  }

  return (
    <div className={className}>
      {mobileRender ? (
        <ul className="divide-y divide-line md:hidden">
          {rows.map((row, i) => (
            <li key={rowKey(row, i)}>{mobileRender(row, i)}</li>
          ))}
        </ul>
      ) : null}
      <div className={cn("overflow-x-auto", mobileRender && "hidden md:block")}>
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b border-line">
              {columns.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  className={cn(
                    "h-11 px-4 text-sm font-semibold text-ink-muted",
                    c.align === "end" && "text-right",
                    c.hideBelowLg && "hidden lg:table-cell",
                    c.className,
                  )}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((row, i) => (
              <tr
                key={rowKey(row, i)}
                onClick={clickable ? () => activate(row) : undefined}
                onKeyDown={
                  clickable
                    ? (e) => {
                        if (e.key === "Enter") activate(row);
                      }
                    : undefined
                }
                tabIndex={clickable ? 0 : undefined}
                className={cn(clickable && "cursor-pointer transition-colors duration-150 hover:bg-canvas-subtle focus-visible:bg-canvas-subtle")}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cn(
                      "h-16 px-4 align-middle text-base text-ink",
                      c.align === "end" && "text-right tnum",
                      c.hideBelowLg && "hidden lg:table-cell",
                      c.className,
                    )}
                  >
                    {c.render(row, i)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {nextCursor && onLoadMore ? (
        <div className="flex justify-center pt-4">
          <Button variant="secondary" loading={loadingMore} onClick={() => onLoadMore(nextCursor)}>
            Cargar más
          </Button>
        </div>
      ) : null}
    </div>
  );
}
