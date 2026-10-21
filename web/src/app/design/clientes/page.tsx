import type { Metadata } from "next";
import { AdminShell } from "@/components/layout/AdminShell";
import { ClientesMuestra } from "../_muestras/ClientesMuestra";
import { MUESTRA_NEGOCIO, MUESTRA_TASA } from "../_muestras/fixtures";

export const metadata: Metadata = { title: "Muestra: clientes" };

export default function ClientesMuestraPage() {
  return (
    <AdminShell businessName={MUESTRA_NEGOCIO} rate={MUESTRA_TASA} activePath="/admin/clientes">
      <ClientesMuestra />
    </AdminShell>
  );
}
