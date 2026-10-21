import Link from "next/link";
import { type ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export type CircleTone = "neutral" | "debt" | "favor" | "brand" | "strong" | "muted";

const CIRCLE: Record<CircleTone, string> = {
  neutral: "bg-canvas-subtle text-ink",
  debt: "bg-debt-subtle text-debt",
  favor: "bg-favor-subtle text-favor",
  brand: "bg-brand-subtle text-brand-ink",
  strong: "bg-primary text-on-primary",
  muted: "bg-canvas-subtle text-ink-faint",
};

/** Ícono en círculo de 40 px: la marca de cada fila (movimiento, método, cliente). */
export function IconCircle({ tone = "neutral", children, className }: { tone?: CircleTone; children: ReactNode; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn("inline-flex size-10 shrink-0 items-center justify-center rounded-pill [&>svg]:size-5", CIRCLE[tone], className)}
    >
      {children}
    </span>
  );
}

/** Iniciales del cliente en círculo ("Bodega El Samán" → "BE"). */
export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials =
    name
      .replace(/[^\p{L}\p{N}\s]/gu, " ")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]?.toLocaleUpperCase("es-VE"))
      .join("") || "·";
  return (
    <span
      aria-hidden
      className={cn("inline-flex size-10 shrink-0 items-center justify-center rounded-pill bg-canvas-subtle text-sm font-bold text-ink", className)}
    >
      {initials}
    </span>
  );
}

export type ListRowProps = {
  leading?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  /** Columna derecha: monto, chip. */
  trailing?: ReactNode;
  href?: string;
  onClick?: () => void;
  /** Muestra el chevron de navegación (por defecto, cuando hay `href`). */
  chevron?: boolean;
  /** Fila tachada (anulada o revertida): sigue legible y en el historial. */
  struck?: boolean;
  className?: string;
  "aria-label"?: string;
};

/**
 * Fila de lista de app de delivery: círculo, título, subtítulo y valor a la derecha.
 * Con `href` es un enlace; con `onClick`, un botón; sin ninguno, un `div`.
 */
export function ListRow({ leading, title, subtitle, trailing, href, onClick, chevron, struck, className, ...aria }: ListRowProps) {
  const showChevron = chevron ?? !!href;
  const body = (
    <>
      {leading}
      <span className="flex min-w-0 flex-1 flex-col">
        <span className={cn("line-clamp-2 break-words text-base font-semibold text-ink", struck && "text-ink-muted line-through decoration-1")}>{title}</span>
        {subtitle ? <span className="truncate text-sm text-ink-muted">{subtitle}</span> : null}
      </span>
      {trailing ? <span className="flex shrink-0 flex-col items-end gap-1 text-right">{trailing}</span> : null}
      {showChevron ? <ChevronRight aria-hidden className="size-5 shrink-0 text-ink-faint" /> : null}
    </>
  );
  const base = cn("flex min-h-16 w-full items-center gap-3 px-4 py-3 text-left", className);
  const interactive = "transition-colors duration-150 ease-out hover:bg-canvas-subtle active:bg-surface-sunken";
  if (href) {
    return (
      <Link href={href} className={cn(base, interactive)} aria-label={aria["aria-label"]}>
        {body}
      </Link>
    );
  }
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={cn(base, interactive)} aria-label={aria["aria-label"]}>
        {body}
      </button>
    );
  }
  return <div className={base}>{body}</div>;
}
