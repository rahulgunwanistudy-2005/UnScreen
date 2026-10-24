import { expect, test } from '@playwright/test';

test('audible preview is off by default and stops when screen-reader mode is turned on', async ({ page }) => {
	await page.addInitScript(() => {
		const spoken: string[] = [];
		Object.defineProperty(window, 'speechSynthesis', { value: {
			speaking: false,
			pending: false,
			cancel: () => spoken.push('[cancel]'),
			speak: (utterance: SpeechSynthesisUtterance) => spoken.push(utterance.text)
		} });
		Object.assign(window, { __previewSpoken: spoken });
	});
	const spokenSoFar = () => page.evaluate(() => (window as unknown as { __previewSpoken: string[] }).__previewSpoken);
	await page.goto('/app');
	const screenReader = page.getByLabel('I am using a screen reader', { exact: true });
	const hear = page.getByLabel('Hear it: speak announcements aloud', { exact: true });
	await expect(hear).toBeVisible();
	await expect(screenReader).not.toBeChecked();
	await expect(hear).not.toBeChecked();
	await expect(hear).toBeEnabled();
	await page.keyboard.press('Alt+Shift+KeyW');
	expect((await spokenSoFar()).filter((s) => s !== '[cancel]')).toEqual([]);
	await hear.check();
	await page.keyboard.press('Alt+Shift+KeyW');
	await expect.poll(spokenSoFar).toContain('Not reading.');
	await screenReader.check();
	await expect(hear).not.toBeChecked();
	await expect(hear).toBeDisabled();
	const spoken = await spokenSoFar();
	expect(spoken).toContain('[cancel]');
	await page.keyboard.press('Alt+Shift+KeyW');
	expect(await spokenSoFar()).toEqual(spoken);
	await page.reload();
	await expect(hear).not.toBeChecked();
});
