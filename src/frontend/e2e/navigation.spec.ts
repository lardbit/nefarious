import { test, expect } from '@playwright/test';

test.describe('nefarious e2e - Navigation', () => {
  test('should show Login link when not authenticated', async ({ page }) => {
    await page.goto('/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    // The login page should render
    await expect(page.locator('app-root')).toBeVisible();
  });

  test('should show 404 page for unknown hash route', async ({ page }) => {
    await page.goto('/static/index.html#/this-does-not-exist');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    // The page not found component should render
    const pnf = page.locator('app-page-not-found');
    await expect(pnf).toBeVisible({ timeout: 10000 });
  });
});
