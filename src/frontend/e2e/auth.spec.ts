import { test, expect } from '@playwright/test';

test.describe('nefarious e2e - Authentication', () => {
  test('should load the login page with app-root', async ({ page }) => {
    await page.goto('/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    const appRoot = page.locator('app-root');
    await expect(appRoot).toBeVisible();
  });

  test('should boot the Angular app and show navbar', async ({ page }) => {
    await page.goto('/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    // Wait for Angular to finish bootstrapping
    await page.waitForTimeout(3000);
    // Check if navbar elements are rendered
    const navbar = page.locator('.navbar');
    await expect(navbar).toBeVisible({ timeout: 10000 });
  });

  test('should show the navbar brand', async ({ page }) => {
    await page.goto('/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    const brand = page.locator('.navbar-brand');
    // The brand element should be visible
    await expect(brand).toBeVisible({ timeout: 10000 });
  });
});
