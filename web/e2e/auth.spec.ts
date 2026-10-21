import { expect, test } from "@playwright/test";

/** Acceso sin sesión (proxy.ts) y validación local del login. No necesita la API. */
test("sin sesión, /admin manda a /login conservando la página", async ({ page }) => {
  await page.goto("/admin/clientes?filtro=vencidos");
  await expect(page).toHaveURL(/\/login\?next=%2Fadmin%2Fclientes%3Ffiltro%3Dvencidos$/);
  await expect(page.getByRole("heading", { name: "Entra al panel" })).toBeVisible();
});

test("el login pide un teléfono venezolano válido", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Teléfono").fill("123");
  await page.getByLabel("Contraseña", { exact: true }).fill("una-clave");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.locator("form").getByRole("alert")).toHaveText("Revisa el teléfono: escríbelo como 0414-123.45.67.");
});

test("cerrar sesión desde otro origen se rechaza", async ({ request }) => {
  const res = await request.post("/api/auth/logout", { headers: { Origin: "https://otro-sitio.example" }, maxRedirects: 0 });
  expect(res.status()).toBe(403);
});
