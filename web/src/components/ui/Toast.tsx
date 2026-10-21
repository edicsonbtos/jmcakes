"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { CircleCheck, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastTone = "default" | "error";
type ToastItem = { id: number; message: string; tone: ToastTone };

type ToastApi = { show: (message: string, opts?: { tone?: ToastTone }) => void };

const ToastContext = createContext<ToastApi | null>(null);

const DURATION_MS = 3200;

/**
 * Confirmación breve, abajo y al centro, en píldora negra: "Abono de $20,00 registrado".
 * Se anuncia con `aria-live="polite"`; los errores, con `assertive`.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const seq = useRef(0);

  const show = useCallback((message: string, opts?: { tone?: ToastTone }) => {
    seq.current += 1;
    const item = { id: seq.current, message, tone: opts?.tone ?? "default" };
    setItems((prev) => [...prev.slice(-2), item]);
  }, []);

  const dismiss = useCallback((id: number) => setItems((prev) => prev.filter((t) => t.id !== id)), []);
  const api = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-[max(1.5rem,env(safe-area-inset-bottom))] z-50 flex flex-col items-center gap-2 px-4"
      >
        {items.map((t) => (
          <ToastBubble key={t.id} item={t} onDone={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastBubble({ item, onDone }: { item: ToastItem; onDone: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDone(item.id), DURATION_MS);
    return () => clearTimeout(timer);
  }, [item.id, onDone]);
  const Icon = item.tone === "error" ? TriangleAlert : CircleCheck;
  return (
    <div
      role={item.tone === "error" ? "alert" : "status"}
      className={cn(
        "pointer-events-auto flex max-w-md items-center gap-2.5 rounded-pill px-5 py-3 text-base font-semibold shadow-popover animate-toast-in",
        item.tone === "error" ? "bg-debt text-canvas" : "bg-primary text-on-primary",
      )}
    >
      <Icon aria-hidden className="size-5 shrink-0" strokeWidth={2.25} />
      <span>{item.message}</span>
    </div>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast necesita <ToastProvider> (está en el layout raíz).");
  return ctx;
}
