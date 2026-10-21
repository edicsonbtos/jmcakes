import { describe, expect, it } from "vitest";
import { fromScaled, groupDecimal, isDecimal, normalizeAmountInput, sign, toScaled } from "../money";
import { caracasDay, fmtBs, fmtDate, fmtDateBig, fmtDateTime, fmtDayMonth, fmtQty, fmtRate, fmtRelativeDay, fmtTime, fmtUsd } from "../format";
import { formatVePhone, normalizeVePhone, whatsappLink } from "../phone";

describe("money (string decimal, sin float)", () => {
  it("escala y redondea HALF_UP como la API", () => {
    expect(toScaled("1234.565")).toBe(123457n);
    expect(toScaled("-0.005")).toBe(-1n);
    expect(toScaled("0.1")).toBe(10n);
    expect(fromScaled(123457n)).toBe("1234.57");
    expect(fromScaled(-5n)).toBe("-0.05");
  });

  it("suma 0.1 + 0.2 exacto cuando se trabaja escalado", () => {
    expect(fromScaled(toScaled("0.1") + toScaled("0.2"))).toBe("0.30");
  });

  it("detecta el signo y valida decimales", () => {
    expect(sign("-4.00")).toBe(-1);
    expect(sign("0.00")).toBe(0);
    expect(sign("97")).toBe(1);
    expect(isDecimal("12.50")).toBe(true);
    expect(isDecimal("12,50")).toBe(false);
    expect(() => toScaled("abc")).toThrow();
  });

  it("normaliza lo que escribe el dueño y rechaza miles", () => {
    expect(normalizeAmountInput("12,5")).toBe("12.50");
    expect(normalizeAmountInput("$ 12.50")).toBe("12.50");
    expect(normalizeAmountInput("1.234,56")).toBeNull();
    expect(normalizeAmountInput("12,345")).toBeNull();
    expect(normalizeAmountInput("-10")).toBeNull();
    expect(normalizeAmountInput("-10", { allowNegative: true })).toBe("-10.00");
    expect(normalizeAmountInput("−10,5", { allowNegative: true })).toBe("-10.50");
    expect(normalizeAmountInput("")).toBeNull();
  });

  it("agrupa miles con punto y decimales con coma", () => {
    expect(groupDecimal("1234567.5")).toBe("1.234.567,50");
  });
});

describe("format (es-VE, hora de Caracas)", () => {
  it("formatea USD y Bs con signo opcional", () => {
    expect(fmtUsd("1234.5")).toBe("$1.234,50");
    expect(fmtUsd("-20")).toBe("−$20,00");
    expect(fmtUsd("36", { signed: true })).toBe("+$36,00");
    expect(fmtUsd("-4.00", { abs: true })).toBe("$4,00");
    expect(fmtBs("17964.4")).toBe("Bs 17.964,40");
  });

  it("muestra la tasa con 2 a 4 decimales y cantidades sin ceros sobrantes", () => {
    expect(fmtRate("185.2000")).toBe("Bs 185,20");
    expect(fmtRate("185.2045")).toBe("Bs 185,2045");
    expect(fmtQty("2.500")).toBe("2,5");
    expect(fmtQty("12")).toBe("12");
  });

  it("usa el día de Caracas aunque la máquina esté en UTC", () => {
    // 22:30 VET del 13 = 02:30 UTC del 14.
    const iso = "2026-10-14T02:30:00Z";
    expect(caracasDay(iso)).toBe("2026-10-13");
    expect(fmtDayMonth(iso)).toBe("13/10");
    expect(fmtDate(iso)).toMatch(/^13 oct 2026$/);
    expect(fmtTime(iso)).toMatch(/10:30/);
    expect(fmtDateBig(iso)).toMatch(/^martes 13 de octubre$/);
  });

  it("dice Hoy y Ayer según Caracas", () => {
    const now = new Date("2026-10-21T19:30:00Z"); // 3:30 p. m. VET del 21
    expect(fmtRelativeDay("2026-10-21T04:30:00Z", now)).toBe("Hoy"); // 00:30 VET del 21
    expect(fmtRelativeDay("2026-10-21T03:30:00Z", now)).toBe("Ayer"); // 23:30 VET del 20
    expect(fmtRelativeDay("2026-10-12T13:15:00Z", now)).toBe("12 oct");
    expect(fmtDateTime("2026-10-21T14:12:00Z", now)).toMatch(/^Hoy · 10:12/);
  });
});

describe("phone", () => {
  it("normaliza a E.164 venezolano", () => {
    expect(normalizeVePhone("0414-123.45.67")).toBe("+584141234567");
    expect(normalizeVePhone("+58 414 1234567")).toBe("+584141234567");
    expect(normalizeVePhone("4141234567")).toBe("+584141234567");
    expect(normalizeVePhone("123")).toBeNull();
  });

  it("lo muestra como lo dicta el dueño y arma el enlace de WhatsApp", () => {
    expect(formatVePhone("+584245550177")).toBe("0424-555.01.77");
    expect(formatVePhone(null)).toBe("");
    expect(whatsappLink("+584141234567", "Debe $5,00")).toBe("https://wa.me/584141234567?text=Debe%20%245%2C00");
  });
});
