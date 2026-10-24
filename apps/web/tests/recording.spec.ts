import { expect, test } from '@playwright/test';

test('genuine recorded session replays in the reader with stable focus and no model requests', async ({ page }) => {
	let engineRequests = 0;
	await page.route('**/v1/session', (route) => { engineRequests++; return route.abort(); });
	await page.clock.install();
	await page.goto('/app');
	await page.getByRole('button', { name: 'Watch a recorded session' }).click();
	await expect(page.getByText('Recorded session, played at 2× speed.', { exact: true })).toBeVisible();
	await page.clock.runFor(10);
	await expect(page.locator('main table caption')).toBeVisible();
	const cell = page.locator('main table tbody tr').first().locator('th, td').nth(1);
	await cell.focus();
	const handle = await cell.elementHandle();
	await page.clock.runFor(15_000);
	expect(await page.evaluate((el) => document.activeElement === el, handle)).toBe(true);
	await page.clock.runFor(75_000);
	await expect(page.locator('#status-line')).toContainText('Recording complete');
	await expect(page.getByRole('button', { name: 'Ask', exact: true })).toBeDisabled();
	expect(engineRequests).toBe(0);
});
