import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const routes = ['/', '/app', '/help', '/benchmark', '/privacy'];

for (const scheme of ['light', 'dark'] as const) {
	for (const route of routes) {
		test(`${route} has no axe violations (${scheme})`, async ({ page }) => {
			await page.emulateMedia({ colorScheme: scheme });
			await page.goto(route);
			await page.waitForLoadState('networkidle');
			const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
			expect(results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
		});
	}
}

test('settings dialog has no axe violations', async ({ page }) => {
	await page.goto('/app');
	await page.getByRole('button', { name: 'Settings' }).click();
	const results = await new AxeBuilder({ page }).include('dialog').analyze();
	expect(results.violations.map((v) => v.id)).toEqual([]);
});

test('landing hero after the animation has no axe violations', async ({ page }) => {
	await page.goto('/');
	await page.getByRole('button', { name: 'Skip to the table' }).click();
	await expect(page.getByRole('region', { name: 'Rebuilt table, scrollable' })).toBeVisible();
	const results = await new AxeBuilder({ page }).include('figure').analyze();
	expect(results.violations.map((v) => v.id)).toEqual([]);
});
