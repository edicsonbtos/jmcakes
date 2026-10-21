"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

export type ChipOption<T extends string> = { value: T; label: ReactNode; count?: number | null };

/**
 * Chips de filtro (una sola opción activa). La selección se marca con el naranja de horno,
 * único uso del color de marca junto al foco. Cada chip mide 40 px y su zona táctil, 48 px.
 */
export function FilterChips<T extends string>({
  options,
  value,
  onChange,
  label,
  className,
}: {
  options: ReadonlyArray<ChipOption<T>>;
  value: T;
  onChange: (value: T) => void;
  /** Nombre del grupo para lectores de pantalla, p. ej. "Filtrar clientes". */
  label: string;
  className?: string;
}) {
  return (
    <div role="group" aria-label={label} className={cn("flex flex-wrap items-center gap-2 py-1", className)}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "relative inline-flex h-10 items-center gap-1.5 rounded-pill border-[1.5px] px-4 text-sm font-semibold transition-[background-color,border-color,color] duration-150 ease-out",
              "after:absolute after:inset-x-0 after:-inset-y-1 after:content-['']",
              active
                ? "border-brand bg-brand-subtle text-brand-ink"
                : "border-line bg-surface text-ink hover:border-line-strong",
            )}
          >
            {o.label}
            {typeof o.count === "number" ? <span className="tnum font-medium opacity-80">{o.count}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

/** Control segmentado (radio): Detal / Mayor, USD / Bs. */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  label,
  className,
  name,
}: {
  options: ReadonlyArray<{ value: T; label: ReactNode }>;
  value: T;
  onChange: (value: T) => void;
  label: string;
  className?: string;
  /** Para enviar el valor en un `<form>`. */
  name?: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className={cn("grid auto-cols-fr grid-flow-col gap-1 rounded-md bg-canvas-subtle p-1", className)}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "h-10 rounded-sm px-3 text-sm font-bold transition-[background-color,color] duration-150 ease-out",
              active ? "bg-surface text-ink ring-[1.5px] ring-brand" : "text-ink-muted hover:text-ink",
            )}
          >
            {o.label}
          </button>
        );
      })}
      {name ? <input type="hidden" name={name} value={value} /> : null}
    </div>
  );
}
