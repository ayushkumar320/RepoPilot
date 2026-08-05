import { expect, test } from "@playwright/test";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

// The provider dialog is a native <dialog> driven by showModal(), so the
// dismissal paths it inherits from the platform (Escape, backdrop click) are
// the part worth pinning down — they are invisible in the markup.
test.beforeEach(async ({ page }) => {
  await page.route(
    new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    async (route) => {
      if (route.request().url().includes("/account/usage")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            free_repositories_remaining: 1,
            free_questions_remaining: 5,
            provider_connected: false,
            groq_connected: false,
            huggingface_connected: false,
            credential_storage: "session_only",
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    },
  );
  await page.goto("/");
});

const dialog = "dialog.provider-dialog";

test("opens modally and traps focus inside", async ({ page }) => {
  await page.getByRole("button", { name: /free questions/i }).click();

  await expect(page.locator(dialog)).toBeVisible();
  // showModal() (not show()) is what makes the rest of the page inert.
  await expect(page.locator(`${dialog}[open]`)).toHaveCount(1);
  await expect(page.locator(dialog)).toHaveJSProperty("open", true);

  const focusInsideDialog = await page.evaluate(() =>
    document.querySelector("dialog.provider-dialog")?.contains(document.activeElement),
  );
  expect(focusInsideDialog).toBe(true);
});

test("Escape closes it", async ({ page }) => {
  await page.getByRole("button", { name: /free questions/i }).click();
  await expect(page.locator(dialog)).toBeVisible();

  await page.keyboard.press("Escape");

  await expect(page.locator(dialog)).toBeHidden();
});

test("clicking the backdrop closes it, clicking the panel does not", async ({ page }) => {
  await page.getByRole("button", { name: /free questions/i }).click();
  await expect(page.locator(dialog)).toBeVisible();

  // A click on the panel must not bubble into a dismissal.
  await page.locator(".provider-dialog-content").click({ position: { x: 5, y: 5 } });
  await expect(page.locator(dialog)).toBeVisible();

  // The backdrop is outside the dialog box, so click by viewport corner.
  await page.mouse.click(5, 5);
  await expect(page.locator(dialog)).toBeHidden();
});
