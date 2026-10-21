import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Estado vacío que enseña qué hacer (no "Sin datos"): ícono en círculo, título,
 * una frase y, si aplica, la acción que lo resuelve.
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center px-6 py-12 text-center", className)}>
      {icon ? (
        <span aria-hidden className="mb-4 inline-flex size-14 items-center justify-center rounded-pill bg-canvas-subtle text-ink [&>svg]:size-6">
          {icon}
        </span>
      ) : null}
      <p className="text-lg font-bold text-ink">{title}</p>
      {description ? <p className="mt-1 max-w-sm text-base text-ink-muted">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
