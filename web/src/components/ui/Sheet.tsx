// Adaptado de OpenGravity: apps/web/src/components/ui/Modal.tsx (reescrito sobre <dialog>)
"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { IconButton } from "./Button";

export type SheetProps = {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  /** Barra inferior fija con la acción principal (p. ej. "Registrar abono"). */
  footer?: ReactNode;
  /** No se cierra con Escape ni tocando fuera mientras se guarda. */
  busy?: boolean;
  className?: string;
};

/**
 * Hoja inferior en el teléfono y diálogo centrado desde 640 px. Sobre `<dialog>` con
 * `showModal()`: foco atrapado, Escape y el resto de la página inerte sin librerías.
 */
export function Sheet({ open, onClose, title, description, children, footer, busy = false, className }: SheetProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onCancel = (e: Event) => {
      e.preventDefault();
      if (!busy) onClose();
    };
    el.addEventListener("cancel", onCancel);
    return () => el.removeEventListener("cancel", onCancel);
  }, [busy, onClose]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
      className={cn(
        // Teléfono: pegada abajo, ancho completo, esquinas superiores redondeadas.
        "fixed inset-x-0 bottom-0 top-auto m-0 hidden max-h-[92dvh] w-full max-w-none flex-col rounded-t-sheet bg-surface-raised p-0 text-ink shadow-sheet",
        "open:flex open:animate-sheet-up",
        // Desde 640 px: diálogo centrado.
        "sm:inset-0 sm:m-auto sm:h-fit sm:max-h-[88dvh] sm:w-[min(100%-2rem,32rem)] sm:rounded-lg sm:open:animate-fade-in",
        className,
      )}
    >
      <div aria-hidden className="mx-auto mt-2 h-1 w-10 shrink-0 rounded-pill bg-line-strong sm:hidden" />
      <header className="flex shrink-0 items-start gap-2 px-5 pb-2 pt-3 sm:pt-5">
        <div className="min-w-0 flex-1 pt-2">
          <h2 id={titleId} className="text-xl font-heavy text-ink">
            {title}
          </h2>
          {description ? (
            <p id={descId} className="mt-1 text-sm text-ink-muted">
              {description}
            </p>
          ) : null}
        </div>
        <IconButton label="Cerrar" onClick={onClose} disabled={busy} className="-mr-2">
          <X aria-hidden className="size-6" />
        </IconButton>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 pb-5">{children}</div>
      {footer ? (
        <footer className="shrink-0 border-t border-line bg-surface-raised px-5 pb-[max(1rem,env(safe-area-inset-bottom))] pt-4">
          {footer}
        </footer>
      ) : null}
    </dialog>
  );
}
