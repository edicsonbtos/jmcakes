import { AdminShell } from "@/components/layout/AdminShell";
import { getTodayRate, rateSummary } from "@/lib/rates";
import { displayBusinessName, getPublicSettings } from "@/lib/settings";

/**
 * Layout del panel (`/admin/**` y `/cambiar-contrasena`). `proxy.ts` ya verificó la sesión,
 * el rol ADMIN y `mustChangePassword` antes de llegar aquí.
 */
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const [settings, rate] = await Promise.all([getPublicSettings(), getTodayRate()]);
  return (
    <AdminShell businessName={displayBusinessName(settings)} rate={rateSummary(rate)}>
      {children}
    </AdminShell>
  );
}
