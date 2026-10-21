import { expect, test } from '@playwright/test';

type Op = { op: 'add' | 'remove' | 'replace'; path: string; value: unknown };

const box = { x0: 0, y0: 0, x1: 10, y1: 10 };
const cell = (id: string, text: string) => ({ id, text, bbox: box, confidence: 0.95, unreadable: false, uncertain: false });
const row = (r: number, values: string[]) => ({ id: `r${r}`, key: values[0], cells: values.map((v, j) => cell(`r${r}.c${j + 1}`, v)) });

const doc = {
	version: 1,
	content_type: 'sheet',
	title: 'Q3 Pipeline',
	content_bbox: { x0: 0, y0: 0, x1: 1000, y1: 1000 },
	sheet: {
		columns: ['Account', 'Owner', 'Q3 revenue'].map((h, j) => cell(`c${j + 1}`, h)),
		header_rows: 1,
		rows: [
			row(1, ['Acme Corp', 'Asha Rao', '$1.1M']),
			row(2, ['Globex', 'Ben Okafor', '$0.4M']),
			row(3, ['Initech', 'Chen Wei', '$2.0M']),
			row(4, ['Hooli', 'Diya Menon', '$0.9M'])
		],
		sheet_name: 'Pipeline'
	},
	code: null,
	blocks: null
};

test('focus and element identity survive 20 patches', async ({ page }) => {
	await page.goto('/fixture/reader');
	await page.waitForFunction(() => (window as unknown as { __ready?: boolean }).__ready === true);
	await page.evaluate((d) => (window as unknown as { __snapshot: (d: unknown) => void }).__snapshot(d), doc);

	const target = page.locator('[data-ref="r2.c3"]');
	await target.focus();
	const handle = await target.elementHandle();
	const table = await page.locator('table').elementHandle();

	const ops: Op[][] = [];
	for (let k = 0; k < 20; k++) {
		const step: Op[] = [];
		if (k % 5 === 4) step.push({ op: 'add', path: '/sheet/rows/0', value: row(100 + k, [`New ${k}`, 'Elif Kaya', `$${k}.0M`]) });
		else if (k % 5 === 2) step.push({ op: 'remove', path: '/sheet/rows/0', value: null });
		else if (k % 5 === 3) step.push({ op: 'replace', path: `/sheet/rows/${'__r2__'}/cells/2/text`, value: `$0.${k}M` });
		else step.push({ op: 'replace', path: '/sheet/rows/__last__/cells/1/text', value: `Owner ${k}` });
		ops.push(step);
	}

	for (let k = 0; k < ops.length; k++) {
		const applied = await page.evaluate(
			({ step, version }) => {
				const rows = [...document.querySelectorAll('tbody tr')].map((tr) => tr.getAttribute('data-ref'));
				const resolved = step.map((o) => ({
					...o,
					path: o.path.replace('__r2__', String(rows.indexOf('r2'))).replace('__last__', String(rows.length - 1))
				}));
				return (window as unknown as { __patch: (v: number, b: number, ops: unknown[]) => boolean }).__patch(
					version + 1,
					version,
					resolved
				);
			},
			{ step: ops[k], version: k + 1 }
		);
		expect(applied).toBe(true);
		const same = await page.evaluate(([el, t]) => document.activeElement === el && document.contains(t), [handle, table]);
		expect(same, `focus lost after patch ${k + 1}`).toBe(true);
	}
	await expect(target).toHaveText('$0.18M');
	await expect(page.locator('tbody tr')).toHaveCount(4);
});
