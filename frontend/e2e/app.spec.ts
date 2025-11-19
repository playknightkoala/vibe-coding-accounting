import { test, expect } from '@playwright/test';

test.describe('Accounting App E2E', () => {
    const password = 'Test@1234';

    test.beforeEach(async ({ page }) => {
        page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));

        // Register and Login
        await page.goto('/register');

        const uniqueUsername = `u${Date.now()}`;
        console.log(`Testing with username: ${uniqueUsername}`);

        await page.fill('input#username', uniqueUsername);
        await page.evaluate(() => document.getElementById('username')?.blur());

        await page.fill('input#password', password);
        await page.dispatchEvent('input#password', 'input');

        const submitBtn = page.locator('button[type="submit"]');
        await expect(submitBtn).toBeEnabled();
        await submitBtn.click();

        try {
            await expect(page.locator('text=註冊成功！')).toBeVisible({ timeout: 5000 });
        } catch (e) {
            const errorModal = page.locator('text=註冊失敗');
            if (await errorModal.isVisible()) {
                const errorMsg = await page.locator('.modal-content p').nth(1).textContent();
                console.error(`Registration failed: ${errorMsg}`);
                throw new Error(`Registration failed: ${errorMsg}`);
            }
            throw e;
        }

        await page.click('button:has-text("前往登入")');

        await expect(page).toHaveURL(/\/login/);
        await page.fill('input#username', uniqueUsername);
        await page.fill('input#password', password);
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL('/');
    });

    test('should load the home page', async ({ page }) => {
        await expect(page).toHaveTitle(/會計與預算系統/);
        await expect(page.locator('h1')).toBeVisible();
    });

    test('should have accounts or allow creating one', async ({ page }) => {
        await page.click('text=帳戶');
        await expect(page).toHaveURL(/\/accounts/);

        const noAccounts = page.locator('text=尚無帳戶');
        await expect(noAccounts).toBeVisible();

        await page.click('button:has-text("新增帳戶")');

        // Wait for modal
        await expect(page.locator('.modal')).toBeVisible();

        // Fill form inside modal
        // The input doesn't have ID, but it's the first input in the form
        await page.locator('.modal input').first().fill('E2E Test Account');

        await page.click('button:has-text("建立")');

        await expect(page.locator('table')).toContainText('E2E Test Account');
    });

    test('should create a transaction', async ({ page }) => {
        // Create Account first
        await page.click('text=帳戶');
        await page.click('button:has-text("新增帳戶")');
        await expect(page.locator('.modal')).toBeVisible();
        await page.locator('.modal input').first().fill('Trans Account');
        await page.click('button:has-text("建立")');

        // Go to Transactions
        await page.click('text=交易');
        await page.click('button:has-text("新增交易")');
        await expect(page.locator('.modal')).toBeVisible();

        // Fill form
        // Description is the second input? No, let's check Transactions.vue
        // Account select is first.
        // Description input is second (first input type=text).
        // Amount is input type=number.

        // We can use labels to find inputs
        await page.fill('label:has-text("描述") + input', 'E2E Transaction');
        await page.fill('label:has-text("金額") + input', '100');

        await page.click('button:has-text("建立")');

        await expect(page.locator('table')).toContainText('E2E Transaction');
    });
});
