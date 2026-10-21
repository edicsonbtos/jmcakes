/**
 * DATOS DE EJEMPLO para /design (no son clientes reales). Forma tomada de 08:
 * `AdminCustomer` (+ `balance`, `balanceVes`) y `statement.rows`. Los montos y Bs vienen
 * escritos como los devolvería la API; aquí no se calcula dinero salvo en `mockFiadoQuote`,
 * que hace de `POST /fiado/quote` solo para que la muestra responda.
 * TODO(contrato): cambiar por los tipos de `api-types.ts` en G1.
 */
import { fromScaled, toScaled } from "@/lib/money";

export const MUESTRA_NEGOCIO = "Panadería de ejemplo";
export const MUESTRA_TASA = { label: "Tasa BCV de hoy", value: "Bs 185,20" };
/** "Ahora" fijo para que las capturas no cambien: martes 21 oct 2026, 3:30 p. m. en Caracas. */
export const MUESTRA_AHORA = new Date("2026-10-21T19:30:00Z");

export type CustomerType = "RETAIL" | "WHOLESALE";

export type MuestraCliente = {
  id: string;
  contactName: string;
  businessName: string | null;
  notes: string | null;
  phone: string | null;
  type: CustomerType;
  creditDays: number;
  creditLimit: string;
  balance: string;
  balanceVes: string | null;
  overdueDebt: string;
};

export const CLIENTES: MuestraCliente[] = [
  { id: "c1", contactName: "Bodega El Samán", businessName: "Bodega El Samán", notes: null, phone: "+584245550177", type: "WHOLESALE", creditDays: 7, creditLimit: "60.00", balance: "97.00", balanceVes: "17964.40", overdueDebt: "61.00" },
  { id: "c2", contactName: "Perros Los Panas", businessName: "Perros Los Panas", notes: "frente a la plaza", phone: "+584125550193", type: "WHOLESALE", creditDays: 3, creditLimit: "0.00", balance: "73.50", balanceVes: "13612.20", overdueDebt: "73.50" },
  { id: "c3", contactName: "Café La Esquina", businessName: "Café La Esquina", notes: null, phone: "+584145550108", type: "WHOLESALE", creditDays: 7, creditLimit: "100.00", balance: "54.00", balanceVes: "10000.80", overdueDebt: "0.00" },
  { id: "c4", contactName: "Sra. Carmen Rojas", businessName: null, notes: "la del kiosko", phone: "+584145550121", type: "RETAIL", creditDays: 7, creditLimit: "0.00", balance: "19.50", balanceVes: "3611.40", overdueDebt: "18.50" },
  { id: "c5", contactName: "Kiosko San José", businessName: "Kiosko San José", notes: null, phone: "+584245550122", type: "WHOLESALE", creditDays: 7, creditLimit: "0.00", balance: "48.00", balanceVes: "8889.60", overdueDebt: "0.00" },
  { id: "c6", contactName: "Yolimar Pérez", businessName: null, notes: "vecina del 3B", phone: null, type: "RETAIL", creditDays: 7, creditLimit: "0.00", balance: "9.00", balanceVes: "1666.80", overdueDebt: "6.00" },
  { id: "c7", contactName: "Hermanos Rivas", businessName: "Abasto Hermanos Rivas", notes: null, phone: "+584165550144", type: "WHOLESALE", creditDays: 15, creditLimit: "200.00", balance: "126.40", balanceVes: "23409.28", overdueDebt: "0.00" },
  { id: "c8", contactName: "Sr. Luis Méndez", businessName: null, notes: null, phone: "+584165550140", type: "RETAIL", creditDays: 7, creditLimit: "0.00", balance: "-4.00", balanceVes: "-740.80", overdueDebt: "0.00" },
  { id: "c9", contactName: "Sra. Elena Díaz", businessName: null, notes: null, phone: "+584145550111", type: "RETAIL", creditDays: 7, creditLimit: "0.00", balance: "0.00", balanceVes: "0.00", overdueDebt: "0.00" },
];

/** Lo que daría `GET /admin/dashboard/summary` (`receivables`) para estos clientes. */
export const POR_COBRAR = { total: "427.40", totalVes: "79154.48", retail: "28.50", wholesale: "398.90" };

export type StatementKind = "SALDO_ANTERIOR" | "FIADO" | "ABONO" | "ANULACION" | "REVERSO" | "AJUSTE";

export type StatementRow = {
  seq: number;
  at: string;
  kind: StatementKind;
  description: string;
  amount: string;
  balanceAfter: string;
  actorName: string;
  receivableId?: string;
  paymentId?: string;
  /** Marcado por la API cuando el fiado fue anulado o el abono revertido. */
  voided?: boolean;
};

/** Estado de cuenta de "Bodega El Samán" (c1), de lo más nuevo a lo más viejo. */
export const MOVIMIENTOS_C1: StatementRow[] = [
  { seq: 7, at: "2026-10-21T14:20:00Z", kind: "ANULACION", description: "Anulado: 2 Pan de perro (paquete 8) · Se registró dos veces", amount: "-3.60", balanceAfter: "97.00", actorName: "María", receivableId: "r6" },
  { seq: 6, at: "2026-10-21T14:12:00Z", kind: "FIADO", description: "2 Pan de perro (paquete 8)", amount: "3.60", balanceAfter: "100.60", actorName: "María", receivableId: "r6", voided: true },
  { seq: 5, at: "2026-10-20T16:05:00Z", kind: "ABONO", description: "Zelle · ref. ZL-88213", amount: "-15.00", balanceAfter: "97.00", actorName: "Admin", paymentId: "p2" },
  { seq: 4, at: "2026-10-18T12:40:00Z", kind: "FIADO", description: "30 Cachito de jamón", amount: "36.00", balanceAfter: "112.00", actorName: "Admin", receivableId: "r3" },
  { seq: 3, at: "2026-10-12T13:15:00Z", kind: "FIADO", description: "80 Canilla, 24 Golfeado", amount: "56.00", balanceAfter: "76.00", actorName: "Admin", receivableId: "r2" },
  { seq: 2, at: "2026-10-09T15:30:00Z", kind: "ABONO", description: "Pago móvil · ref. 004512 · Bs 3.704,00", amount: "-20.00", balanceAfter: "20.00", actorName: "Admin", paymentId: "p1" },
  { seq: 1, at: "2026-10-06T13:00:00Z", kind: "FIADO", description: "60 Canilla, 20 Pan sobado", amount: "40.00", balanceAfter: "40.00", actorName: "Admin", receivableId: "r1" },
];

/** Lo que daría `manual-payment/quote` para un abono por pago móvil de Bs 3.704,00. */
export const ABONO_QUOTE = {
  amountLocal: "3704.00",
  amountUsd: "20.00",
  rate: { date: "2026-10-21", value: "185.20", isFallback: false },
  balanceBefore: "97.00",
  balanceAfter: "77.00",
  balanceAfterVes: "14260.40",
};

export const ABONO_FILA: StatementRow = {
  seq: 8,
  at: "2026-10-21T19:30:00Z",
  kind: "ABONO",
  description: "Pago móvil · ref. 118204 · Bs 3.704,00",
  amount: "-20.00",
  balanceAfter: "77.00",
  actorName: "Admin",
  paymentId: "p3",
};

export type MuestraProducto = { id: string; name: string; unitLabel: string; price: string; retailPrice: string | null };

export const PRODUCTOS: MuestraProducto[] = [
  { id: "p1", name: "Canilla", unitLabel: "unidad", price: "0.40", retailPrice: "0.50" },
  { id: "p2", name: "Pan campesino", unitLabel: "unidad", price: "1.20", retailPrice: "1.50" },
  { id: "p3", name: "Cachito de jamón", unitLabel: "unidad", price: "1.20", retailPrice: "1.50" },
  { id: "p4", name: "Golfeado", unitLabel: "unidad", price: "1.00", retailPrice: "1.20" },
  { id: "p5", name: "Pan sobado", unitLabel: "unidad", price: "0.80", retailPrice: "1.00" },
  { id: "p6", name: "Pan de perro (paquete 8)", unitLabel: "paquete", price: "1.80", retailPrice: null },
];

/**
 * Simula `POST /admin/customers/{id}/fiado/quote` para la muestra (en el panel real lo
 * calcula la API). Precio mayor para WHOLESALE; total por línea redondeado a 2 decimales.
 */
export function mockFiadoQuote(
  lines: { productId: string; qty: string }[],
  balanceBefore: string,
  creditLimit: string,
): { total: string; balanceAfter: string; warning: string | null } {
  let total = 0n;
  for (const l of lines) {
    const p = PRODUCTOS.find((x) => x.id === l.productId);
    if (!p) continue;
    const qty = toScaled(l.qty || "0", 3);
    const price = toScaled(p.price, 2);
    total += (qty * price + 500n) / 1000n;
  }
  const after = toScaled(balanceBefore, 2) + total;
  const limit = toScaled(creditLimit, 2);
  const warning = limit > 0n && after > limit ? `Supera el límite de crédito ($${fromScaled(limit).replace(".", ",")}). Se registra igual.` : null;
  return { total: fromScaled(total), balanceAfter: fromScaled(after), warning };
}
