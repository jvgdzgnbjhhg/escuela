import { expect, test } from "@playwright/test";

test("acceso accesible y adaptable", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Evaluación académica");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Cada avance");
  await expect(page.getByLabel("Correo electrónico")).toBeVisible();
  await expect(page.getByRole("button", { name: "Iniciar sesión" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("el servidor frontend tiene health check", async ({ request }) => {
  const response = await request.get("/api/health");
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ok" });
});

test("el proxy protege rutas, sesión y origen", async ({ request }) => {
  expect((await request.get("/api/v1/students")).status()).toBe(401);
  expect((await request.get("/api/v1/unknown")).status()).toBe(404);
  expect((await request.post("/api/v1/auth/login", { data: {} })).status()).toBe(403);
});
