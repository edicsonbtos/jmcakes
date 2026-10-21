import { cn } from "@/lib/utils";

/** Bloque que reserva el lugar del contenido mientras carga (no un spinner en medio). */
export function Skeleton({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "block rounded-sm bg-[linear-gradient(90deg,var(--color-canvas-subtle)_25%,var(--color-surface-sunken)_50%,var(--color-canvas-subtle)_75%)] bg-[length:200%_100%] animate-shimmer",
        className,
      )}
    />
  );
}

/** Filas de lista en carga: círculo + dos líneas + monto, como `ListRow`. */
export function SkeletonRows({ rows = 5, label = "Cargando…" }: { rows?: number; label?: string }) {
  return (
    <div role="status" aria-label={label} className="divide-y divide-line">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3">
          <Skeleton className="size-10 rounded-pill" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-1/4" />
          </div>
          <Skeleton className="h-5 w-20" />
        </div>
      ))}
    </div>
  );
}
