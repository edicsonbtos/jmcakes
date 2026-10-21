import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";

/** Indicador de espera dentro de un control. Para contenido que carga, usa `Skeleton`. */
export function Spinner({ className, label }: { className?: string; label?: string }) {
  return (
    <LoaderCircle
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? "img" : undefined}
      className={cn("size-5 shrink-0 animate-spin", className)}
      strokeWidth={2.25}
    />
  );
}
