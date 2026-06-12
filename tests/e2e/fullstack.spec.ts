import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

async function getAuthToken(username: string, password: string): Promise<string> {
  const response = await fetch(`${BASE}/api/auth/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  return data.token;
}

test.describe('Full-stack e2e', () => {
  let authToken: string;

  test.beforeAll(async () => {
    authToken = await getAuthToken('admin', 'admin');
  });

  test('API authentication works', async () => {
    expect(authToken).toBeTruthy();
    expect(typeof authToken).toBe('string');
  });

  test('API returns current user', async ({ request }) => {
    const response = await request.get(`${BASE}/api/user/`, {
      headers: { Authorization: `Token ${authToken}` },
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    expect(data[0].username).toBe('admin');
  });

  test('API returns settings', async ({ request }) => {
    const response = await request.get(`${BASE}/api/settings/`, {
      headers: { Authorization: `Token ${authToken}` },
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('language');
    }
  });

  test('API returns quality profiles', async ({ request }) => {
    const response = await request.get(`${BASE}/api/quality-profile/`, {
      headers: { Authorization: `Token ${authToken}` },
    });
    expect(response.status()).toBe(200);
  });

  test('API returns qualities list', async ({ request }) => {
    const response = await request.get(`${BASE}/api/qualities/`, {
      headers: { Authorization: `Token ${authToken}` },
    });
    expect(response.status()).toBe(200);
  });

  test('API returns media categories', async ({ request }) => {
    const response = await request.get(`${BASE}/api/media-categories/`, {
      headers: { Authorization: `Token ${authToken}` },
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('mediaCategories');
  });

  test('Frontend loads and shows app root', async ({ page }) => {
    await page.goto(`${BASE}/static/index.html#/login`);
    await page.waitForSelector('app-root', { timeout: 15000 });
    await expect(page.locator('app-root')).toBeVisible();
  });

  test('Frontend login page renders with form', async ({ page }) => {
    await page.goto(`${BASE}/static/index.html#/login`);
    await page.waitForSelector('app-root', { timeout: 15000 });
    await page.waitForTimeout(3000);
    // The login component should render
    await expect(page.locator('app-root')).toBeVisible();
    await expect(page.locator('.navbar-brand')).toBeVisible({ timeout: 10000 });
  });
});
