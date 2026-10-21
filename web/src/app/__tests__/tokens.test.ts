// @vitest-environment node
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const root = path.resolve(__dirname, "../../../..");
const tokens = JSON.parse(readFileSync(path.join(root, "docs/design/tokens.json"), "utf8"));
const css = readFileSync(path.resolve(__dirname, "../globals.css"), "utf8");

function block(selector: string): string {
  const start = css.indexOf(selector);
  expect(start, `falta el bloque ${selector}`).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf("}", start));
}

describe("globals.css sigue a docs/design/tokens.json", () => {
  it("cada color claro está en @theme", () => {
    const theme = block("@theme {");
    for (const [name, value] of Object.entries<string>(tokens.color.light)) {
      expect(theme, `--color-${name}`).toContain(`--color-${name}: ${value};`);
    }
  });

  it("cada color oscuro está en los dos bloques de oscuro", () => {
    for (const sel of [':root:not([data-theme="light"]) {', ':root[data-theme="dark"] {']) {
      const dark = block(sel);
      for (const [name, value] of Object.entries<string>(tokens.color.dark)) {
        expect(dark, `${sel} --color-${name}`).toContain(`--color-${name}: ${value};`);
      }
    }
  });

  it("radios, tamaños de texto y movimiento coinciden", () => {
    for (const [name, value] of Object.entries<string>(tokens.radius)) expect(css).toContain(`--radius-${name}: ${value};`);
    for (const [name, v] of Object.entries<{ size: string; line: string }>(tokens.font.scale)) {
      expect(css).toContain(`--text-${name}: ${v.size};`);
      expect(css).toContain(`--text-${name}--line-height: ${v.line};`);
    }
    expect(css).toContain(`--ease-out: ${tokens.motion["ease-out"]};`);
    expect(css).toContain(`--duration-amount: ${tokens.motion.amount};`);
  });

  it("no quedan colores fuera del sistema en los componentes", () => {
    // Nada de la paleta por defecto de Tailwind (slate, sky, gray…): solo roles.
    expect(css).toContain("--color-*: initial;");
  });
});
