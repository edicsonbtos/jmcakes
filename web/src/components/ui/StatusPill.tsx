// Adaptado de OpenGravity: apps/web/src/components/ui/Badge.tsx
import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

export type PillTone = "debt" | "favor" | "warn" | "neutral" | "brand" | "strong";

const TONES: Record<PillTone, string> = {
  debt: "bg-debt-subtle text-debt",
  favor: "bg-favor-subtle text-favor",
  warn: "bg-warn-subtle text-warn",
  neutral: "bg-canvas-subtle text-ink-muted",
  brand: "bg-brand-subtle text-brand-ink",
  strong: "bg-primary text-on-primary",
};

/**
 * Estado con texto (nunca solo color, PRODUCT.md §Accessibility): "Vencido", "Detal",
 * "Anulado", "A favor"… El punto refuerza, el texto informa.
 */
export function StatusPill({
  tone = "neutral",
  children,
  dot = false,
  className,
}: {
  tone?: PillTone;
  children: ReactNode;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-pill px-2.5 text-xs font-bold tnum",
        TONES[tone],
        className,
      )}
    >
      {dot ? <span aria-hidden className="size-1.5 rounded-pill bg-current" /> : null}
      {children}
    </span>
  );
}
