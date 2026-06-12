import { test, expect } from '@playwright/test';

test.describe('nefarious e2e - Search', () => {
  test('should load app for search page', async ({ page }) => {
    await page.goto('/static/index.html#/search/auto');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    // The app should load (may show login or search depending on auth)
    await expect(page.locator('app-root')).toBeVisible();
  });

  test('should load app for discover page', async ({ page }) => {
    await page.goto('/static/index.html#/discover');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('app-root')).toBeVisible();
  });
});
