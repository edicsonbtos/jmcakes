import { businessInitial } from "@/lib/brand";
import { cn } from "@/lib/utils";

/**
 * Marca del negocio: inicial en un círculo naranja de horno y el nombre de la configuración
 * (`business.name`). El logo real del dueño reemplaza el círculo cuando exista.
 */
export function BrandMark({ name, compact = false, className }: { name: string; compact?: boolean; className?: string }) {
  return (
    <span className={cn("inline-flex min-w-0 items-center gap-2.5", className)}>
      <span
        aria-hidden
        className="inline-flex size-9 shrink-0 items-center justify-center rounded-pill bg-brand text-lg font-heavy leading-none text-on-brand"
      >
        {businessInitial(name)}
      </span>
      <span className={cn("truncate font-heavy text-ink [font-stretch:92%]", compact ? "text-base" : "text-lg")}>{name}</span>
    </span>
  );
}
