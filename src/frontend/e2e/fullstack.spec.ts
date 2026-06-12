import { test, expect } from '@playwright/test';

test.describe('Full-stack e2e', () => {

  test('Frontend serves index.html', async ({ request }) => {
    const response = await request.get('http://localhost:8000/static/index.html');
    expect(response.status()).toBe(200);
    const body = await response.text();
    expect(body).toContain('app-root');
    expect(body).toContain('<html');
  });

  test('Frontend loads app with hash routing', async ({ page }) => {
    await page.goto('http://localhost:8000/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await expect(page.locator('app-root')).toBeVisible();
  });

  test('Frontend shows navbar on login page', async ({ page }) => {
    await page.goto('http://localhost:8000/static/index.html#/login');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('.navbar-brand')).toBeVisible({ timeout: 10000 });
  });

  test('Frontend shows 404 page for unknown route', async ({ page }) => {
    await page.goto('http://localhost:8000/static/index.html#/this-does-not-exist');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('app-page-not-found')).toBeVisible({ timeout: 10000 });
  });

  test('Frontend loads search page', async ({ page }) => {
    await page.goto('http://localhost:8000/static/index.html#/search/auto');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('app-root')).toBeVisible();
  });

  test('Frontend loads discover page', async ({ page }) => {
    await page.goto('http://localhost:8000/static/index.html#/discover');
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('app-root')).toBeVisible();
  });
});
