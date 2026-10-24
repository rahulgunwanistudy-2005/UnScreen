import { expect, test } from '@playwright/test';

test('audible preview requires opting out of screen-reader mode and stops when re-enabled', async ({ page }) => {
	await page.addInitScript(() => {
		const spoken: string[] = [];
		Object.defineProperty(window, 'speechSynthesis', { value: {
			cancel: () => spoken.push('[cancel]'),
			speak: (utterance: SpeechSynthesisUtterance) => spoken.push(utterance.text)
		} });
		Object.assign(window, { __previewSpoken: spoken });
	});
	await page.goto('/app');
	await page.getByText('Hear announcements without a screen reader', { exact: true }).click();
	const screenReader = page.getByLabel('I am using a screen reader', { exact: true });
	const hear = page.getByLabel('Hear it: speak announcements aloud', { exact: true });
	await expect(screenReader).toBeChecked();
	await expect(hear).not.toBeChecked();
	await expect(hear).toBeDisabled();
	await screenReader.uncheck();
	await hear.check();
	await page.keyboard.press('Alt+Shift+KeyW');
	await expect.poll(() => page.evaluate(() => (window as unknown as { __previewSpoken: string[] }).__previewSpoken)).toContain('Not reading.');
	await screenReader.check();
	await expect(hear).not.toBeChecked();
	await expect(hear).toBeDisabled();
	const spoken = await page.evaluate(() => (window as unknown as { __previewSpoken: string[] }).__previewSpoken);
	expect(spoken).toContain('[cancel]');
	await page.keyboard.press('Alt+Shift+KeyW');
	expect(await page.evaluate(() => (window as unknown as { __previewSpoken: string[] }).__previewSpoken)).toEqual(spoken);
	await page.reload();
	await page.getByText('Hear announcements without a screen reader', { exact: true }).click();
	await expect(screenReader).toBeChecked();
	await expect(hear).not.toBeChecked();
});
