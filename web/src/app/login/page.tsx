// Adaptado de OpenGravity: apps/web/src/app/login/page.tsx (solo el layout visual)
import type { Metadata } from "next";
import { InlineAlert } from "@/components/ui";
import { BrandMark } from "@/components/layout/BrandMark";
import { safeNext } from "@/lib/auth-guard";
import { displayBusinessName, getPublicSettings } from "@/lib/settings";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = { title: "Entrar" };

const MOTIVOS: Record<string, { tone: "info" | "warn" | "error"; text: string }> = {
  salida: { tone: "info", text: "Cerraste sesión. Vuelve a entrar cuando quieras." },
  rol: { tone: "warn", text: "Este usuario no tiene acceso al panel." },
  red: { tone: "error", text: "Sin conexión con el servidor. Revisa tu señal e intenta de nuevo." },
};

export default async function LoginPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const next = safeNext(typeof params.next === "string" ? params.next : null);
  const motivo = typeof params.motivo === "string" ? MOTIVOS[params.motivo] : undefined;
  const name = displayBusinessName(await getPublicSettings());

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-[26rem] flex-col px-4 pb-10 pt-6 sm:justify-center sm:pt-10">
      <BrandMark name={name} />
      <div className="mt-12 sm:mt-10">
        <h1 className="text-3xl font-heavy text-ink">Entra al panel</h1>
        <p className="mt-2 text-base text-ink-muted">Con tu teléfono y tu contraseña.</p>
      </div>
      {motivo ? (
        <InlineAlert tone={motivo.tone} className="mt-6">
          {motivo.text}
        </InlineAlert>
      ) : null}
      <div className="mt-8">
        <LoginForm next={next} />
      </div>
      <p className="mt-8 text-sm text-ink-muted">
        ¿Olvidaste la contraseña? Pídele a otro administrador que te la restablezca desde Configuración.
      </p>
    </main>
  );
}
