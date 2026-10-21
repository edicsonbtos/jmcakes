import { type ReactNode } from "react";
import { CircleCheck, Info, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

export type AlertTone = "error" | "warn" | "info" | "success";

const TONES: Record<AlertTone, { box: string; Icon: typeof Info }> = {
  error: { box: "bg-debt-subtle text-debt", Icon: TriangleAlert },
  warn: { box: "bg-warn-subtle text-warn", Icon: TriangleAlert },
  info: { box: "bg-canvas-subtle text-ink", Icon: Info },
  success: { box: "bg-favor-subtle text-favor", Icon: CircleCheck },
};

/**
 * Aviso dentro del flujo: el `detail` de la API tal cual, la advertencia de límite de
 * crédito ("Se registra igual"), una confirmación. Errores con `role="alert"`.
 */
export function InlineAlert({
  tone = "info",
  title,
  children,
  className,
}: {
  tone?: AlertTone;
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  const { box, Icon } = TONES[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn("flex items-start gap-3 rounded-md px-4 py-3 text-sm", box, className)}
    >
      <Icon aria-hidden className="mt-0.5 size-5 shrink-0" strokeWidth={2.25} />
      <div className="min-w-0">
        {title ? <p className="font-bold">{title}</p> : null}
        {children ? <div className={cn("font-medium", title && "mt-0.5")}>{children}</div> : null}
      </div>
    </div>
  );
}
