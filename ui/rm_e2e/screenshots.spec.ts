import path from "node:path";
import { test, expect } from "@fixtures/admin";
import type { Page, TestInfo } from "@playwright/test";
import {
  SCREENSHOTS_ENABLED,
  THEME,
  SCREENSHOT_LANGUAGES,
  SCREENSHOT_DIR,
  captureFullPage,
} from "@helpers/screenshots";
import {
  gotoProductRoute,
  setLanguage,
  suppressProductOnboarding,
} from "@helpers/product";

const screenshotPath = (testInfo: TestInfo, lang: string, name: string) =>
  path.join(SCREENSHOT_DIR, THEME, testInfo.project.name, lang, `${name}.png`);

async function reloadWithOnboardingSuppressed(page: Page): Promise<void> {
  await suppressProductOnboarding(page, "matrix");
  await page.reload();
  await expect(page.getByTestId("home-page")).toBeVisible();
}

test.describe("screenshots", () => {
  test.skip(!SCREENSHOTS_ENABLED, "set SCREENSHOTS=1 to capture screenshots");

  for (const lang of SCREENSHOT_LANGUAGES) {
    test.describe(`language: ${lang}`, () => {
      test("core screenshots", async ({ page }, testInfo) => {
        await setLanguage(page, lang);

        await gotoProductRoute(page, "matrix");
        await expect(page.getByTestId("home-page")).toBeVisible();

        // First-time onboarding dialog
        const onboardingDialog = page.getByTestId("onboarding-dialog");
        if (await onboardingDialog.isVisible().catch(() => false)) {
          await captureFullPage(
            page,
            screenshotPath(testInfo, lang, "first-time-guide-dialog"),
          );
        }

        await reloadWithOnboardingSuppressed(page);

        await captureFullPage(page, screenshotPath(testInfo, lang, "home"));
      });
    });
  }
});
