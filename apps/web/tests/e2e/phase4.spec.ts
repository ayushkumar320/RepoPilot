import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";

test("phase 4 tour starts and shows synchronized viewer shell", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Repo URL").fill(repoUrl);
  await page.getByRole("button", { name: "Index And Continue" }).click();

  await expect(page.getByText("Why Are You Here?")).toBeVisible();

  await page.getByRole("button", { name: "I want to learn this codebase" }).click();
  await page.getByRole("button", { name: "Start Tour" }).click();

  await expect(page.getByText("Tour View")).toBeVisible();
  await expect(page.getByText("Synchronized Code Viewer")).toBeVisible();
});
