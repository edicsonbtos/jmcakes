// Adaptado de OpenGravity: apps/web/src/components/ui/Switch.tsx
"use client";

import { useId, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export type SwitchProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: ReactNode;
  description?: ReactNode;
  disabled?: boolean;
  className?: string;
};

/** Interruptor accesible (`role="switch"`) con su etiqueta; toda la fila es tocable. */
export function Switch({ checked, onChange, label, description, disabled, className }: SwitchProps) {
  const id = useId();
  return (
    <div className={cn("flex min-h-12 items-center justify-between gap-4", className)}>
      <label htmlFor={id} className="flex min-w-0 flex-col">
        <span className="text-base font-semibold text-ink">{label}</span>
        {description ? <span className="text-sm text-ink-muted">{description}</span> : null}
      </label>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-8 w-13 shrink-0 items-center rounded-pill transition-colors duration-200 ease-out disabled:cursor-not-allowed disabled:opacity-50",
          checked ? "bg-primary" : "bg-line-strong",
        )}
      >
        <span
          aria-hidden
          className={cn(
            "absolute left-1 size-6 rounded-pill bg-surface shadow-popover transition-transform duration-200 ease-out",
            checked ? "translate-x-5" : "translate-x-0",
          )}
        />
      </button>
    </div>
  );
}
