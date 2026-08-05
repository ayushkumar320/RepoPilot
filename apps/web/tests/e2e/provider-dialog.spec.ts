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
  await page.getByRole("button", { name: /connect your provider/i }).click();

  await expect(page.locator(dialog)).toBeVisible();
  // showModal() (not show()) is what makes the rest of the page inert.
  await expect(page.locator(`${dialog}[open]`)).toHaveCount(1);
  await expect(page.locator(dialog)).toHaveJSProperty("open", true);

  const focusInsideDialog = await page.evaluate(() =>
    document.querySelector("dialog.provider-dialog")?.contains(document.activeElement),
  );
  expect(focusInsideDialog).toBe(true);
});

test("it animates in rather than appearing fully formed", async ({ page }) => {
  // @starting-style is what gives a dialog an entrance at all — without it
  // showModal() paints the final state on the first frame.
  const entrance = await page.evaluate(() => {
    const node = document.querySelector<HTMLDialogElement>("dialog.provider-dialog");
    if (!node) return { error: "no dialog" };
    (document.querySelector(".usage-control") as HTMLButtonElement).click();
    return new Promise((resolve) => {
      requestAnimationFrame(() =>
        requestAnimationFrame(() =>
          resolve({
            transitioning: node
              .getAnimations()
              .map((a) => (a as CSSTransition).transitionProperty ?? "")
              .filter(Boolean),
          }),
        ),
      );
    });
  });

  const result = entrance as Record<string, unknown>;
  expect(result.error, "dialog was not found").toBeUndefined();
  expect(result.transitioning, "dialog appeared with no entrance transition").toContain("opacity");
  expect(result.transitioning, "dialog did not scale in").toContain("transform");
});

test("Escape closes it", async ({ page }) => {
  await page.getByRole("button", { name: /connect your provider/i }).click();
  await expect(page.locator(dialog)).toBeVisible();

  await page.keyboard.press("Escape");

  await expect(page.locator(dialog)).toBeHidden();
});

test("it animates out instead of vanishing on close", async ({ page }) => {
  await page.getByRole("button", { name: /connect your provider/i }).click();
  await expect(page.locator(dialog)).toBeVisible();
  // Let the entrance finish so we are only measuring the exit.
  await page.waitForTimeout(700);

  const exit = await page.evaluate(() => {
    const node = document.querySelector<HTMLDialogElement>("dialog.provider-dialog");
    if (!node) return { error: "no dialog" };
    (document.querySelector(".dialog-actions button") as HTMLButtonElement).click();
    // Sampled on the frame after the close: the element must still be laid
    // out and still hold the top layer while its transition plays.
    return new Promise((resolve) => {
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          const style = getComputedStyle(node);
          resolve({
            stillRendered: style.display !== "none",
            stillInTopLayer: style.overlay !== "none",
            // Which properties are mid-transition. Asserting on the running
            // set rather than a sampled opacity value keeps this independent
            // of how far the transition happens to have advanced.
            transitioning: node
              .getAnimations()
              .map((a) => (a as CSSTransition).transitionProperty ?? "")
              .filter(Boolean),
          });
        }),
      );
    });
  });

  assertExit(exit);
  // And it does eventually leave.
  await expect(page.locator(dialog)).toBeHidden();
});

function assertExit(exit: unknown): void {
  const result = exit as Record<string, unknown>;
  expect(result.error, "dialog was not found").toBeUndefined();
  expect(result.stillRendered, "dialog was removed from layout on the same frame").toBe(true);
  expect(result.stillInTopLayer, "dialog dropped out of the top layer mid-exit").toBe(true);
  expect(result.transitioning, "nothing was transitioning on the way out").toContain("opacity");
}

test("clicking the backdrop closes it, clicking the panel does not", async ({ page }) => {
  await page.getByRole("button", { name: /connect your provider/i }).click();
  await expect(page.locator(dialog)).toBeVisible();

  // A click on the panel must not bubble into a dismissal.
  await page.locator(".provider-dialog-content").click({ position: { x: 5, y: 5 } });
  await expect(page.locator(dialog)).toBeVisible();

  // The backdrop is outside the dialog box, so click by viewport corner.
  await page.mouse.click(5, 5);
  await expect(page.locator(dialog)).toBeHidden();
});
