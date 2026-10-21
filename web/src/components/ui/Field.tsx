// Adaptado de OpenGravity: apps/web/src/components/ui/{Input,Select,Textarea}.tsx
"use client";

import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

type FieldChrome = {
  label: ReactNode;
  /** Ayuda corta debajo del campo. */
  hint?: ReactNode;
  /** Mensaje de error (texto de la API o de validación local). */
  error?: ReactNode;
  /** Oculta la etiqueta visualmente (sigue para lectores de pantalla). */
  hideLabel?: boolean;
  className?: string;
};

/** Caja gris sin borde; al enfocar, borde de tinta de 2 px (como el buscador de una app de delivery). */
const BOX =
  "flex w-full items-center rounded-md border-2 border-transparent bg-canvas-subtle transition-[border-color,background-color] duration-150 ease-out focus-within:border-ink focus-within:bg-surface";
const BOX_ERROR = "border-debt focus-within:border-debt";
const BOX_DISABLED = "opacity-60";

function FieldShell({
  id,
  label,
  hint,
  error,
  hideLabel,
  className,
  children,
}: FieldChrome & { id: string; children: ReactNode }) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className={cn("text-sm font-semibold text-ink", hideLabel && "sr-only")}>
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-sm font-medium text-debt">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-sm text-ink-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function describedBy(id: string, error: unknown, hint: unknown): string | undefined {
  if (error) return `${id}-error`;
  if (hint) return `${id}-hint`;
  return undefined;
}

export type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "prefix" | "size"> &
  FieldChrome & {
    /** Texto o ícono antes del valor, p. ej. "$" o "Bs". */
    prefix?: ReactNode;
    suffix?: ReactNode;
    size?: "md" | "lg";
  };

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, hint, error, hideLabel, className, prefix, suffix, size = "md", id: idProp, disabled, ...rest },
  ref,
) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <div className={cn(BOX, size === "lg" ? "h-14" : "h-12", error && BOX_ERROR, disabled && BOX_DISABLED)}>
        {prefix ? <span className="pl-4 text-base font-semibold text-ink-muted tnum">{prefix}</span> : null}
        <input
          ref={ref}
          id={id}
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, error, hint)}
          className={cn(
            "h-full w-full min-w-0 bg-transparent px-4 text-base text-ink outline-none focus-visible:outline-none disabled:cursor-not-allowed",
            prefix ? "pl-2" : undefined,
            size === "lg" && "text-lg font-semibold",
          )}
          {...rest}
        />
        {suffix ? <span className="flex shrink-0 items-center pr-2">{suffix}</span> : null}
      </div>
    </FieldShell>
  );
});

export type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & FieldChrome;

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, hint, error, hideLabel, className, id: idProp, children, disabled, ...rest },
  ref,
) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <div className={cn(BOX, "relative h-12", error && BOX_ERROR, disabled && BOX_DISABLED)}>
        <select
          ref={ref}
          id={id}
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, error, hint)}
          className="h-full w-full appearance-none bg-transparent pl-4 pr-11 text-base text-ink outline-none focus-visible:outline-none disabled:cursor-not-allowed"
          {...rest}
        >
          {children}
        </select>
        <ChevronDown aria-hidden className="pointer-events-none absolute right-4 size-5 text-ink-muted" />
      </div>
    </FieldShell>
  );
});

export type TextAreaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & FieldChrome;

export const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(function TextAreaField(
  { label, hint, error, hideLabel, className, id: idProp, rows = 3, disabled, ...rest },
  ref,
) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} hideLabel={hideLabel} className={className}>
      <div className={cn(BOX, "items-stretch", error && BOX_ERROR, disabled && BOX_DISABLED)}>
        <textarea
          ref={ref}
          id={id}
          rows={rows}
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, error, hint)}
          className="w-full resize-y bg-transparent px-4 py-3 text-base text-ink outline-none focus-visible:outline-none"
          {...rest}
        />
      </div>
    </FieldShell>
  );
});
