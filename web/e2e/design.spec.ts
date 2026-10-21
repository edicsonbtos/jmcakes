import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

/**
 * Capturas de /design y de las pantallas de muestra (DSN). Se suben como artifact en
 * `web.yml`; el orquestador las baja a `.impeccable/review/` para la revisión de diseño.
 */
const OUT = process.env.CAPTURE_DIR ?? path.resolve(__dirname, "../e2e-capturas");
mkdirSync(OUT, { recursive: true });

async function settle(page: Page) {
  await page.evaluate(() => document.fonts.ready);
  // Sin animaciones de entrada en la captura.
  await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important}" });
}

async function shot(page: Page, name: string, fullPage = true) {
  const project = test.info().project.name;
  await page.screenshot({ path: path.join(OUT, `${project}-${name}.png`), fullPage });
}

for (const scheme of ["light", "dark"] as const) {
  test.describe(`tema ${scheme}`, () => {
    test.use({ colorScheme: scheme });

    test(`/design muestra tokens y componentes (${scheme})`, async ({ page }) => {
      await page.goto("/design");
      await expect(page.getByRole("heading", { name: "Sistema del panel" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Registrar abono" }).first()).toBeVisible();
      await settle(page);
      await shot(page, `design-${scheme}`);
    });

    test(`/login (${scheme})`, async ({ page }) => {
      await page.goto("/login");
      await expect(page.getByRole("heading", { name: "Entra al panel" })).toBeVisible();
      await settle(page);
      await shot(page, `login-${scheme}`);
    });
  });
}

test("ficha del cliente a 390 px: saldo grande y las dos acciones al pulgar", async ({ page }) => {
  test.skip(test.info().project.name !== "mobile", "La ficha se revisa a 390 px.");
  await page.goto("/design/ficha");
  await expect(page.getByText("Debe", { exact: true })).toBeVisible();
  const abonar = page.getByRole("button", { name: "Registrar abono" });
  const fiar = page.getByRole("button", { name: "Fiar productos" });
  await expect(abonar).toBeVisible();
  await expect(fiar).toBeVisible();
  // La barra está fija abajo: el botón queda en el último cuarto de la pantalla.
  const box = await abonar.boundingBox();
  expect(box && box.y > 844 * 0.75).toBeTruthy();
  await settle(page);
  await shot(page, "ficha", false);
  await shot(page, "ficha-completa");

  await abonar.click();
  await expect(page.getByRole("dialog", { name: "Registrar abono" })).toBeVisible();
  await expect(page.getByText(/queda debiendo/)).toBeVisible();
  await shot(page, "ficha-abono", false);
});

test("lista de clientes a 1440 px", async ({ page }) => {
  test.skip(test.info().project.name !== "desktop", "La lista se revisa a 1440 px.");
  await page.goto("/design/clientes");
  await expect(page.getByRole("heading", { name: "Clientes", level: 1 })).toBeVisible();
  await expect(page.getByText("Por cobrar")).toBeVisible();
  await page.getByRole("button", { name: "Vencidos" }).click();
  await expect(page.getByRole("button", { name: "Vencidos" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Todos" }).click();
  await settle(page);
  await shot(page, "clientes");
});
