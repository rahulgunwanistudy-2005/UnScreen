import { expect, test, type Page } from '@playwright/test';

// Full browser loop: real reader app, real capture worker and change gate, real WebSocket and
// engine pipeline. Only the vision model is scripted (it answers from the fixture's truth), so
// this checks the plumbing, not reading accuracy. Accuracy is measured in bench/.

const ENGINE = 'http://localhost:8788';

type Truth = { edits: number; title: string; sheet: { columns: string[]; rows: string[][] } };

async function feedLoop(fixture: Page, app: Page, stop: () => boolean) {
	while (!stop()) {
		const before = await fixture.evaluate(() => window.__truth!());
		const shot = await fixture.screenshot({ type: 'jpeg', quality: 92 });
		const after = await fixture.evaluate(() => window.__truth!());
		if (before.edits === after.edits) {
			await fetch(`${ENGINE}/test/truth`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(after) });
			await app.evaluate((b64) => (window as unknown as { __feed?: (b: string) => Promise<void> }).__feed?.(b64), shot.toString('base64'));
		}
		await new Promise((r) => setTimeout(r, 300));
	}
}

test('a live spreadsheet is rebuilt, edits are announced, and focus survives', async ({ browser }) => {
	const fixtureCtx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
	const appCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
	const fixture = await fixtureCtx.newPage();
	const app = await appCtx.newPage();
	await app.addInitScript(() => {
		navigator.mediaDevices.getDisplayMedia = async () => {
			const c = document.createElement('canvas');
			c.width = 1280;
			c.height = 720;
			const ctx = c.getContext('2d')!;
			(window as unknown as { __feed: (b: string) => Promise<void> }).__feed = async (b64) => {
				const img = new Image();
				img.src = `data:image/jpeg;base64,${b64}`;
				await img.decode();
				ctx.drawImage(img, 0, 0);
			};
			return c.captureStream(5);
		};
	});

	await fixture.goto('/fixture/sheet?seed=5&mode=live&interval=5000&cursor=off');
	await fixture.waitForFunction(() => typeof window.__truth === 'function');
	await app.goto('/app');
	await app.waitForLoadState('networkidle');

	let done = false;
	const feeding = feedLoop(fixture, app, () => done);
	try {
		await app.getByRole('button', { name: 'Start reading the shared screen' }).click();
		const truth0: Truth = (await fixture.evaluate(() => window.__truth!())) as Truth;

		const caption = app.locator('main table caption');
		await expect(caption).toContainText(truth0.title, { timeout: 20_000 });
		await expect(app.locator('[role="status"][aria-live="polite"]')).toContainText('Now showing: Spreadsheet');
		const cells = await app.locator('main table tbody tr').evaluateAll((trs) =>
			trs.map((tr) => [...tr.children].map((c) => c.textContent!.trim()))
		);
		const live: Truth = (await fixture.evaluate(() => window.__truth!())) as Truth;
		expect(cells).toEqual(live.sheet.rows);

		// Hold focus on a cell while the presenter keeps editing.
		const firstCell = app.locator('main table tbody tr').first().locator('th, td').nth(1);
		await firstCell.focus();
		const handle = await firstCell.elementHandle();

		const edited = live.edits;
		await fixture.waitForFunction((n) => window.__truth!().edits > n, edited, { timeout: 15_000 });
		const t1: Truth = (await fixture.evaluate(() => window.__truth!())) as Truth;
		const changed: { row: string; col: string; value: string }[] = [];
		t1.sheet.rows.forEach((r) =>
			r.forEach((v, j) => {
				const prev = live.sheet.rows.find((p) => p[0] === r[0]);
				if (prev && prev[j] !== v) changed.push({ row: r[0], col: t1.sheet.columns[j], value: v });
				else if (!prev && j === 0) changed.push({ row: r[0], col: t1.sheet.columns[0], value: r[0] });
			})
		);
		expect(changed.length).toBeGreaterThan(0);
		const target = changed[0];
		const spoken = app.locator('[role="status"][aria-live="polite"]');
		await expect(spoken).toContainText(target.row, { timeout: 20_000 });
		await expect(app.locator('main table')).toContainText(target.value);
		const sameFocus = await app.evaluate((el) => document.activeElement === el, handle);
		expect(sameFocus).toBe(true);

		// The Changes list records the version.
		await expect(app.getByRole('heading', { name: 'Changes' })).toBeVisible();
		await expect(app.locator('aside ol li').first()).toContainText('Version');
		const historyButton = app.locator('aside ol li').first().getByRole('button');
		const historyHandle = await historyButton.elementHandle();
		await historyButton.click();
		await expect(app.locator('#past-h')).toBeFocused();
		await app.getByRole('button', { name: 'Close this version' }).click();
		expect(await app.evaluate((el) => document.activeElement === el, historyHandle)).toBe(true);
	} finally {
		done = true;
		await feeding;
		await fixtureCtx.close();
		await appCtx.close();
	}
});

test('an upward cursor jump reports the current cell, not the old pointer position', async ({ browser }) => {
	const fixtureCtx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
	const appCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
	const fixture = await fixtureCtx.newPage();
	const app = await appCtx.newPage();
	const settingsSent: { type: string; numeric_style?: string }[] = [];
	app.on('websocket', (ws) => ws.on('framesent', ({ payload }) => {
		if (typeof payload === 'string') { const msg = JSON.parse(payload) as { type: string; numeric_style?: string }; if (msg.type === 'settings') settingsSent.push(msg); }
	}));
	await app.addInitScript(() => {
		localStorage.setItem('unscreen:prefs:v1', JSON.stringify({ numericStyle: 'new_only' }));
		navigator.mediaDevices.getDisplayMedia = async () => {
			const c = document.createElement('canvas'); c.width = 1280; c.height = 720;
			const ctx = c.getContext('2d')!;
			(window as unknown as { __feed: (b: string) => Promise<void> }).__feed = async (b64) => {
				const img = new Image(); img.src = `data:image/jpeg;base64,${b64}`; await img.decode(); ctx.drawImage(img, 0, 0);
			};
			return c.captureStream(5);
		};
	});
	await fixture.goto('/fixture/sheet?seed=3&mode=static&cursor=on');
	await fixture.waitForFunction(() => typeof window.__truth === 'function');
	await app.goto('/app'); await app.waitForLoadState('networkidle');
	let done = false;
	const feeding = feedLoop(fixture, app, () => done);
	try {
		await app.getByRole('button', { name: 'Start reading the shared screen' }).click();
		await expect(app.locator('main table caption')).toBeVisible({ timeout: 20_000 });
		expect(settingsSent.some((m) => m.numeric_style === 'new_only')).toBe(true);
		await fixture.evaluate(() => window.__movePointer!());
		const truth = (await fixture.evaluate(() => window.__truth!())) as Truth;
		await expect(app.locator('aside')).toContainText(`${truth.sheet.rows[0][0]}, Assignee: ${truth.sheet.rows[0][1]}`, { timeout: 10_000 });
		await app.getByRole('button', { name: 'What is the pointer on?' }).click();
		await expect(app.locator('[role="status"][aria-live="polite"]')).toContainText(truth.sheet.rows[0][1]);
	} finally { done = true; await feeding; await fixtureCtx.close(); await appCtx.close(); }
});

test('pipeline overhead without the model: edit to spoken announcement', async ({ browser }) => {
	test.setTimeout(120_000);
	const fixtureCtx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
	const appCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
	const fixture = await fixtureCtx.newPage();
	const app = await appCtx.newPage();
	await app.addInitScript(() => {
		navigator.mediaDevices.getDisplayMedia = async () => {
			const c = document.createElement('canvas');
			c.width = 1280;
			c.height = 720;
			const ctx = c.getContext('2d')!;
			(window as unknown as { __feed: (b: string) => Promise<void> }).__feed = async (b64) => {
				const img = new Image();
				img.src = `data:image/jpeg;base64,${b64}`;
				await img.decode();
				ctx.drawImage(img, 0, 0);
			};
			return c.captureStream(5);
		};
	});
	await fixture.goto('/fixture/sheet?seed=9&mode=live&interval=7000&cursor=off');
	await fixture.waitForFunction(() => typeof window.__truth === 'function');
	await app.goto('/app');
	await app.waitForLoadState('networkidle');
	const spoken: { at: number; text: string }[] = [];
	await app.exposeFunction('__spoken', (text: string) => spoken.push({ at: Date.now(), text }));
	await app.evaluate(() => {
		const live = document.querySelector('[role="status"][aria-live="polite"]')!;
		new MutationObserver(() => (window as unknown as { __spoken: (t: string) => void }).__spoken(live.textContent ?? '')).observe(
			live,
			{ childList: true, characterData: true, subtree: true }
		);
	});
	let done = false;
	const feeding = feedLoop(fixture, app, () => done);
	const latencies: number[] = [];
	try {
		await app.getByRole('button', { name: 'Start reading the shared screen' }).click();
		await expect(app.locator('main table caption')).toBeVisible({ timeout: 20_000 });
		let prev: Truth = (await fixture.evaluate(() => window.__truth!())) as Truth;
		while (latencies.length < 5) {
			await fixture.waitForFunction((n) => window.__truth!().edits > n, prev.edits, { timeout: 20_000, polling: 50 });
			const editAt = Date.now();
			const cur: Truth = (await fixture.evaluate(() => window.__truth!())) as Truth;
			const keys = cur.sheet.rows
				.filter((r) => {
					const p = prev.sheet.rows.find((x) => x[0] === r[0]);
					return !p || p.some((v, j) => v !== r[j]);
				})
				.map((r) => r[0]);
			prev = cur;
			if (keys.length === 0) continue;
			const deadline = editAt + 15_000;
			while (Date.now() < deadline && !spoken.some((s) => s.at >= editAt && keys.some((k) => s.text.includes(k)))) {
				await new Promise((r) => setTimeout(r, 50));
			}
			const hit = spoken.find((s) => s.at >= editAt && keys.some((k) => s.text.includes(k)));
			expect(hit, `no announcement for ${keys.join(', ')}`).toBeTruthy();
			latencies.push(hit!.at - editAt);
		}
	} finally {
		done = true;
		await feeding;
		await fixtureCtx.close();
		await appCtx.close();
	}
	const sorted = [...latencies].sort((a, b) => a - b);
	const report = {
		name: 'pipeline-overhead',
		note: 'Scripted vision model (answers from fixture truth); measures capture, change gate, engine pipeline and announcer only.',
		run_at: new Date().toISOString(),
		edits: latencies.length,
		latencies_ms: latencies,
		p50_ms: sorted[Math.floor((sorted.length - 1) / 2)],
		max_ms: sorted[sorted.length - 1]
	};
	if (process.env.RECORD_RESULTS === '1') {
		const { writeFile, mkdir } = await import('node:fs/promises');
		await mkdir('../../bench/results', { recursive: true });
		await writeFile(`../../bench/results/${report.run_at.slice(0, 10)}-pipeline-overhead.json`, JSON.stringify(report, null, 2));
	}
	console.log(JSON.stringify(report));
	expect(report.max_ms).toBeLessThan(6000);
});
