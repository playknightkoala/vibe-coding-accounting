import { test, expect } from '@playwright/test';

test.describe('Accounting App Full Flow', () => {
    const password = 'Test@1234';

    test.beforeEach(async ({ page }) => {
        // Register and Login
        await page.goto('/register');
        const uniqueUsername = `u${Date.now()}`;
        await page.fill('input#username', uniqueUsername);
        await page.evaluate(() => document.getElementById('username')?.blur());
        await page.fill('input#password', password);
        await page.dispatchEvent('input#password', 'input');

        const submitBtn = page.locator('button[type="submit"]');
        await expect(submitBtn).toBeEnabled();
        await submitBtn.click();

        // Handle registration success/fail
        try {
            await expect(page.locator('text=註冊成功！')).toBeVisible({ timeout: 5000 });
        } catch (e) {
            const errorModal = page.locator('text=註冊失敗');
            if (await errorModal.isVisible()) {
                throw new Error('Registration failed');
            }
            throw e;
        }

        await page.click('button:has-text("前往登入")');
        await page.fill('input#username', uniqueUsername);
        await page.fill('input#password', password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('/');
    });

    test('should complete full user journey', async ({ page }) => {
        // 1. Create Account
        await page.click('text=帳戶');
        await page.click('button:has-text("新增帳戶")');
        await expect(page.locator('.modal')).toBeVisible();
        await page.locator('.modal input').first().fill('Main Account');
        // Default type: Asset, Currency: NTD
        await page.click('button:has-text("建立")');
        await expect(page.locator('table')).toContainText('Main Account');
        await expect(page.locator('table')).toContainText('$0.00');

        // 2. Create Transactions
        await page.click('text=交易');

        // Income: Salary
        await page.click('button:has-text("新增交易")');
        await expect(page.locator('.modal')).toBeVisible();
        await page.fill('label:has-text("描述") + input', 'Salary');
        await page.fill('label:has-text("金額") + input', '5000');
        await page.selectOption('label:has-text("交易類型") + select', 'credit'); // Income
        // Category: Salary (薪資) - assuming it exists or selecting first available
        // Let's just use the default selected category or select one if we know it.
        // Usually "薪資" is in default categories.
        // We can try to select it if it exists, or just leave default.
        // Let's select '薪資' if possible, or just use whatever is first.
        // To be safe, let's just use the first one for now, or check content.

        await page.click('button:has-text("建立")');
        await expect(page.locator('table')).toContainText('Salary');
        await expect(page.locator('table')).toContainText('$5000.00'); // Green color checked visually, text is enough

        // Expense: Lunch
        await page.click('button:has-text("新增交易")');
        await expect(page.locator('.modal')).toBeVisible();
        await page.fill('label:has-text("描述") + input', 'Lunch');
        await page.fill('label:has-text("金額") + input', '100');
        await page.selectOption('label:has-text("交易類型") + select', 'debit'); // Expense
        // Select Category by index 1 to ensure consistency
        const transCategorySelect = page.locator('label:has-text("類別") + div select');
        await transCategorySelect.selectOption({ index: 1 });
        const selectedCategory = await transCategorySelect.inputValue();
        console.log('Selected Transaction Category:', selectedCategory);

        await page.click('button:has-text("建立")');
        await expect(page.locator('table')).toContainText('Lunch');

        // 3. Create Budget
        await page.click('text=預算');
        await page.click('button:has-text("新增預算")');
        await expect(page.locator('.modal')).toBeVisible();

        await page.fill('label:has-text("預算名稱") + input', 'Food Budget');

        // Debug: Log available categories
        const categorySelect = page.locator('label:has-text("類別") + div select');
        const options = await categorySelect.locator('option').allTextContents();
        console.log('Available categories:', options);

        // Select the first available category (index 1, as 0 is placeholder)
        await categorySelect.selectOption({ index: 1 });

        await page.fill('label:has-text("金額") + input', '3000');
        // Account should be auto-selected as Main Account (since it's the only one)

        // Wait for response
        const [response] = await Promise.all([
            page.waitForResponse(res => res.url().includes('/budgets/') && res.status() === 200),
            page.click('button:has-text("建立")')
        ]);

        console.log('Budget creation response:', await response.json());

        // Wait for modal to close or error to appear
        await page.waitForTimeout(1000);

        // Reload to ensure list is updated
        await page.reload();
        await page.waitForLoadState('networkidle');

        // Check for error
        const errorMsg = page.locator('.error');
        if (await errorMsg.isVisible()) {
            console.log('Budget creation error:', await errorMsg.textContent());
        }

        // Verify Budget Card
        // Use a more specific selector to avoid matching the parent card
        const budgetCard = page.locator('.card h3', { hasText: 'Food Budget' }).locator('xpath=..');
        try {
            await expect(budgetCard).toBeVisible({ timeout: 5000 });
        } catch (e) {
            console.log('Page content:', await page.content());
            throw e;
        }
        await expect(budgetCard).toContainText('預算：$3000.00');
        // Verify Used Amount (should be 100 from Lunch)
        await expect(budgetCard).toContainText('已使用：$100.00');
        await expect(budgetCard).toContainText('剩餘：$2900.00');

        // 4. Dashboard Verification
        await page.click('text=儀表板');

        // Verify Account Balance
        // 0 + 5000 - 100 = 4900
        const accountCard = page.locator('.card', { hasText: 'Main Account' });
        await expect(accountCard).toContainText('$4900.00');

        // Verify Recent Transactions
        const recentTrans = page.locator('.card', { hasText: '最近交易' });
        await expect(recentTrans).toContainText('Lunch');
        await expect(recentTrans).toContainText('Salary');

        // Verify Budget Status in Dashboard
        const budgetSection = page.locator('.card', { hasText: '預算狀態' });
        await expect(budgetSection).toContainText('Food Budget');
        await expect(budgetSection).toContainText('已使用：$100.00');
    });
});
