import type { Metadata } from "next";
import { AdminShell } from "@/components/layout/AdminShell";
import { FichaMuestra } from "../_muestras/FichaMuestra";
import { MUESTRA_NEGOCIO, MUESTRA_TASA } from "../_muestras/fixtures";

export const metadata: Metadata = { title: "Muestra: ficha del cliente" };

export default function FichaMuestraPage() {
  return (
    <AdminShell businessName={MUESTRA_NEGOCIO} rate={MUESTRA_TASA} activePath="/admin/clientes/c1">
      <FichaMuestra />
    </AdminShell>
  );
}
