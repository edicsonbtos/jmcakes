"use client";

import { Minus, Plus } from "lucide-react";
import { fromScaled, toScaled } from "@/lib/money";
import { cn } from "@/lib/utils";

const SCALE = 3; // cantidades con hasta 3 decimales (02 §order_items.qty)

/** "2.500" → "2,5"; "" → "0". La cantidad no es dinero, pero tampoco usa float. */
function display(value: string): string {
  if (!value) return "0";
  try {
    return fromScaled(toScaled(value, SCALE), SCALE).replace(/\.?0+$/, "").replace(".", ",") || "0";
  } catch {
    return value;
  }
}

function step(value: string, delta: 1 | -1, min: string): string {
  let current = 0n;
  try {
    current = toScaled(value || "0", SCALE);
  } catch {
    current = 0n;
  }
  const floor = toScaled(min, SCALE);
  const next = current + BigInt(delta) * 10n ** BigInt(SCALE);
  const clamped = next < floor ? floor : next;
  return fromScaled(clamped, SCALE).replace(/\.?0+$/, "") || "0";
}

/**
 * − cantidad + para fiar rápido (09 §Requisitos de uso). Los botones son de 48 px y el
 * número se puede escribir ("1,5" kg). Devuelve la cantidad como string decimal con punto.
 */
export function Stepper({
  value,
  onChange,
  label,
  min = "0",
  className,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  /** Nombre del producto: "Cantidad de Canilla". */
  label: string;
  min?: string;
  className?: string;
  disabled?: boolean;
}) {
  const isZero = !value || /^0+(?:[.,]0*)?$/.test(value);
  return (
    <div className={cn("inline-flex items-center gap-1", className)}>
      <button
        type="button"
        onClick={() => onChange(step(value, -1, min))}
        disabled={disabled || isZero}
        aria-label={`Quitar uno: ${label}`}
        className="inline-flex size-12 items-center justify-center rounded-pill bg-canvas-subtle text-ink transition-[background-color,transform] duration-150 active:scale-95 hover:bg-surface-sunken disabled:text-ink-faint disabled:active:scale-100"
      >
        <Minus aria-hidden className="size-5" strokeWidth={2.5} />
      </button>
      <input
        inputMode="decimal"
        aria-label={`Cantidad de ${label}`}
        value={display(value)}
        disabled={disabled}
        onFocus={(e) => e.currentTarget.select()}
        onChange={(e) => {
          const raw = e.target.value.replace(",", ".").replace(/[^\d.]/g, "");
          if (/^\d*(?:\.\d{0,3})?$/.test(raw)) onChange(raw === "" ? "0" : raw);
        }}
        className={cn(
          "h-12 w-14 rounded-sm bg-transparent text-center text-lg font-bold tnum text-ink outline-none focus-visible:bg-canvas-subtle",
          isZero && "text-ink-faint",
        )}
      />
      <button
        type="button"
        onClick={() => onChange(step(value, 1, min))}
        disabled={disabled}
        aria-label={`Agregar uno: ${label}`}
        className="inline-flex size-12 items-center justify-center rounded-pill bg-primary text-on-primary transition-[background-color,transform] duration-150 active:scale-95 hover:bg-primary-hover disabled:bg-surface-sunken disabled:text-ink-faint"
      >
        <Plus aria-hidden className="size-5" strokeWidth={2.5} />
      </button>
    </div>
  );
}
