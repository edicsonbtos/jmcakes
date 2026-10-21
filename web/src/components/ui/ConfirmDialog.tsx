"use client";

import { useId, useState, type ReactNode } from "react";
import { isApiError } from "@/lib/errors";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { TextField } from "./Field";
import { InlineAlert } from "./InlineAlert";
import { Sheet } from "./Sheet";

export type ConfirmChoice<T extends string> = { value: T; label: string; description?: string };

export type ConfirmDialogProps<T extends string = string> = {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  /** Qué va a pasar con el dinero, en una o dos frases. */
  description?: ReactNode;
  confirmLabel: string;
  /** Anular y revertir son destructivas: botón rojo. */
  tone?: "danger" | "primary";
  /** Motivo obligatorio (09: "Confirmación antes de anular o revertir, con el motivo obligatorio"). */
  reason?: { label?: string; placeholder?: string };
  /** Opciones obligatorias, p. ej. el porqué del reverso (ENTRY_ERROR / BANK_RETURN). */
  choices?: ReadonlyArray<ConfirmChoice<T>>;
  choicesLabel?: string;
  /** Recibe el motivo y la opción; si lanza un `ApiError`, su `detail` se muestra tal cual. */
  onConfirm: (input: { reason: string; choice: T | null }) => Promise<void>;
};

export function ConfirmDialog<T extends string = string>({
  open,
  onClose,
  title,
  description,
  confirmLabel,
  tone = "danger",
  reason,
  choices,
  choicesLabel = "¿Por qué?",
  onConfirm,
}: ConfirmDialogProps<T>) {
  const [text, setText] = useState("");
  const [choice, setChoice] = useState<T | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const formId = useId();
  const groupId = useId();

  const needsReason = !!reason;
  const ready = (!needsReason || text.trim().length > 0) && (!choices || choice !== null);

  const close = () => {
    if (pending) return;
    setText("");
    setChoice(null);
    setError(null);
    onClose();
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!ready || pending) return;
    setPending(true);
    setError(null);
    try {
      await onConfirm({ reason: text.trim(), choice });
      setText("");
      setChoice(null);
      onClose();
    } catch (err) {
      setError(isApiError(err) ? err.detail : "Algo salió mal. Intenta de nuevo.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Sheet
      open={open}
      onClose={close}
      title={title}
      description={description}
      busy={pending}
      footer={
        <div className="grid grid-cols-2 gap-3">
          <Button variant="secondary" onClick={close} disabled={pending}>
            Cancelar
          </Button>
          <Button
            type="submit"
            form={formId}
            variant={tone === "danger" ? "danger" : "primary"}
            loading={pending}
            disabled={!ready}
          >
            {confirmLabel}
          </Button>
        </div>
      }
    >
      <form id={formId} onSubmit={submit} className="flex flex-col gap-4 pt-2">
        {choices ? (
          <fieldset className="flex flex-col gap-2" aria-describedby={groupId}>
            <legend id={groupId} className="mb-1 text-sm font-semibold text-ink">
              {choicesLabel}
            </legend>
            {choices.map((c) => {
              const active = choice === c.value;
              return (
                <label
                  key={c.value}
                  className={cn(
                    "flex min-h-14 cursor-pointer items-start gap-3 rounded-md border-[1.5px] px-4 py-3 transition-colors duration-150",
                    active ? "border-brand bg-brand-subtle" : "border-line hover:border-line-strong",
                  )}
                >
                  <input
                    type="radio"
                    name={`${formId}-choice`}
                    value={c.value}
                    checked={active}
                    onChange={() => setChoice(c.value)}
                    className="mt-1 size-4 accent-[var(--color-brand)]"
                  />
                  <span className="flex flex-col">
                    <span className="text-base font-semibold text-ink">{c.label}</span>
                    {c.description ? <span className="text-sm text-ink-muted">{c.description}</span> : null}
                  </span>
                </label>
              );
            })}
          </fieldset>
        ) : null}
        {needsReason ? (
          <TextField
            label={reason?.label ?? "Motivo (obligatorio)"}
            placeholder={reason?.placeholder}
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
            maxLength={500}
            autoFocus
          />
        ) : null}
        {error ? <InlineAlert tone="error">{error}</InlineAlert> : null}
      </form>
    </Sheet>
  );
}
