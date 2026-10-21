// Adaptado de OpenGravity: apps/web/src/components/ui/Button.tsx
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "md" | "lg";

const VARIANTS: Record<ButtonVariant, string> = {
  // Primario negro (en oscuro, claro): una sola acción principal por vista.
  primary:
    "bg-primary text-on-primary hover:bg-primary-hover disabled:bg-surface-sunken disabled:text-ink-faint",
  secondary: "bg-canvas-subtle text-ink hover:bg-surface-sunken disabled:text-ink-faint",
  ghost: "bg-transparent text-ink hover:bg-canvas-subtle disabled:text-ink-faint",
  danger: "bg-debt-subtle text-debt hover:brightness-95 disabled:bg-canvas-subtle disabled:text-ink-faint",
};

const SIZES: Record<ButtonSize, string> = {
  md: "h-12 px-5 text-base gap-2",
  lg: "h-14 px-6 text-lg gap-2.5",
};

/** Clases del botón, para dar el mismo aspecto a un `<Link>`. */
export function buttonClasses({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
}: { variant?: ButtonVariant; size?: ButtonSize; fullWidth?: boolean; className?: string } = {}): string {
  return cn(
    "relative inline-flex select-none items-center justify-center whitespace-nowrap rounded-md font-bold",
    "transition-[background-color,color,transform,filter] duration-150 ease-out",
    "active:scale-[0.98] disabled:cursor-not-allowed disabled:active:scale-100",
    VARIANTS[variant],
    SIZES[size],
    fullWidth && "w-full",
    className,
  );
}

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  /** Deshabilita el botón y muestra el indicador hasta que llegue la respuesta. */
  loading?: boolean;
  icon?: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", fullWidth, loading = false, icon, className, children, disabled, type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={buttonClasses({ variant, size, fullWidth, className })}
      {...rest}
    >
      {loading ? <Spinner /> : icon}
      <span className="truncate">{children}</span>
    </button>
  );
});

export type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  /** Obligatorio: el botón no tiene texto visible. */
  label: string;
  variant?: "ghost" | "secondary" | "primary";
};

/** Botón redondo de 48 px solo con ícono (cerrar, volver, menú). */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, variant = "ghost", className, children, type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex size-12 shrink-0 items-center justify-center rounded-pill transition-[background-color,transform] duration-150 ease-out active:scale-95 disabled:cursor-not-allowed disabled:text-ink-faint",
        variant === "ghost" && "text-ink hover:bg-canvas-subtle",
        variant === "secondary" && "bg-canvas-subtle text-ink hover:bg-surface-sunken",
        variant === "primary" && "bg-primary text-on-primary hover:bg-primary-hover",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
});
