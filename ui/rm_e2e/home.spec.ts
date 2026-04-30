import { test, expect } from "@fixtures/admin";
import {
  gotoProductRoute,
  setLanguage,
  suppressProductOnboarding,
} from "@helpers/product";

test.describe("matrix home page", () => {
  test.beforeEach(async ({ page }) => {
    await setLanguage(page, "en");
    await suppressProductOnboarding(page, "matrix");

    await gotoProductRoute(page, "matrix");
  });

  test("renders home page with synapse URL and copy button", async ({
    page,
  }) => {
    await expect(page.getByTestId("home-page")).toBeVisible();

    const synapseInput = page.getByTestId("synapse-url-input");
    await expect(synapseInput).toBeVisible();
    await expect(synapseInput).toHaveValue(/^https:\/\/synapse\./);

    await expect(page.getByTestId("synapse-url-copy")).toBeVisible();
    await expect(
      page.getByTestId("feature-guide-button-messaging"),
    ).toBeVisible();
    await expect(page.getByTestId("feature-guide-button-unit")).toBeVisible();
  });

  test("opens messaging feature guide", async ({ page }) => {
    await page.getByTestId("feature-guide-button-messaging").click();

    await expect(page.getByTestId("feature-guide-dialog")).toBeVisible();
    await expect(
      page.getByTestId("feature-guide-step-indicator"),
    ).toContainText("1 /");
    await expect(page.getByTestId("feature-guide-next")).toBeVisible();
  });

  test("opens unit feature guide", async ({ page }) => {
    await page.getByTestId("feature-guide-button-unit").click();

    await expect(page.getByTestId("feature-guide-dialog")).toBeVisible();
    await expect(
      page.getByTestId("feature-guide-step-indicator"),
    ).toContainText("1 /");
    await expect(page.getByTestId("feature-guide-next")).toBeVisible();
  });
});
