import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const outputPath = path.resolve("artifacts/lighthouse.json");
const targetUrl = process.env.LIGHTHOUSE_URL ?? "http://127.0.0.1:3000";

async function main() {
  const lighthouseModule = await import("lighthouse");
  const chromeLauncherModule = await import("chrome-launcher");
  const lighthouse = lighthouseModule.default ?? lighthouseModule;
  const chromeLauncher = chromeLauncherModule.default ?? chromeLauncherModule;

  const chrome = await chromeLauncher.launch({
    chromeFlags: ["--headless", "--no-sandbox", "--disable-dev-shm-usage"],
  });

  try {
    const result = await lighthouse(targetUrl, {
      port: chrome.port,
      output: "json",
      logLevel: "error",
      onlyCategories: ["accessibility"],
    });
    if (!result?.report) {
      throw new Error("Lighthouse did not return a report.");
    }
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, result.report, "utf8");

    const parsed = JSON.parse(result.report);
    const score = parsed.categories.accessibility.score * 100;
    console.log(`Accessibility score: ${score}`);
    if (score < 90) {
      process.exitCode = 1;
    }
  } finally {
    await chrome.kill();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
