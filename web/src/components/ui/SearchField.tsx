"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type SearchFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "type"> & {
  value: string;
  onValueChange: (value: string) => void;
  /** Etiqueta para lectores de pantalla (el campo no lleva etiqueta visible). */
  label: string;
};

/** Buscador en píldora gris, con botón para limpiar. La búsqueda la resuelve el servidor. */
export const SearchField = forwardRef<HTMLInputElement, SearchFieldProps>(function SearchField(
  { value, onValueChange, label, className, placeholder, ...rest },
  ref,
) {
  return (
    <div
      role="search"
      className={cn(
        "flex h-12 w-full items-center gap-2 rounded-pill border-2 border-transparent bg-canvas-subtle pl-4 pr-1 transition-[border-color,background-color] duration-150 ease-out focus-within:border-ink focus-within:bg-surface",
        className,
      )}
    >
      <Search aria-hidden className="size-5 shrink-0 text-ink-muted" strokeWidth={2.25} />
      <input
        ref={ref}
        type="search"
        aria-label={label}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onValueChange(e.target.value)}
        className="h-full w-full min-w-0 bg-transparent text-base text-ink outline-none focus-visible:outline-none"
        autoComplete="off"
        spellCheck={false}
        {...rest}
      />
      {value ? (
        <button
          type="button"
          onClick={() => onValueChange("")}
          aria-label="Limpiar búsqueda"
          className="inline-flex size-10 shrink-0 items-center justify-center rounded-pill text-ink-muted hover:bg-surface-sunken hover:text-ink"
        >
          <X aria-hidden className="size-5" />
        </button>
      ) : null}
    </div>
  );
});
