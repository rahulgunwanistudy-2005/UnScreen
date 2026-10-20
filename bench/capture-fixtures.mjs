// Renders every benchmark fixture through the real /fixture pages and saves the
// screenshot plus the page's own ground truth. Usage: node capture-fixtures.mjs [baseUrl]
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = join(import.meta.dirname, 'fixtures', 'frames');

const SETS = [
	...Array.from({ length: 20 }, (_, i) => ({ kind: 'sheet', seed: 101 + i })),
	...Array.from({ length: 10 }, (_, i) => ({ kind: 'code', seed: 201 + i })),
	...Array.from({ length: 10 }, (_, i) => ({ kind: 'slide', seed: 301 + i }))
];
// 720p and 1080p are plain captures. "meet" is the same content inside a meeting
// window at 1080p; degrade.py turns it into the 1080p-degraded variant.
const VARIANTS = [
	{ name: '720p', width: 1280, height: 720, frame: 'plain' },
	{ name: '1080p', width: 1920, height: 1080, frame: 'plain' },
	{ name: 'meet1080p', width: 1920, height: 1080, frame: 'meet' }
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
const manifest = [];
for (const variant of VARIANTS) {
	const page = await browser.newPage({ viewport: { width: variant.width, height: variant.height } });
	for (const { kind, seed } of SETS) {
		const url = `${BASE}/fixture/${kind}?seed=${seed}&mode=static&frame=${variant.frame}&cursor=off`;
		await page.goto(url, { waitUntil: 'networkidle' });
		await page.waitForFunction(() => typeof window.__truth === 'function');
		const id = `${kind}-${seed}-${variant.name}`;
		const truth = await page.evaluate(() => window.__truth());
		await page.screenshot({ path: join(OUT, `${id}.png`) });
		await writeFile(join(OUT, `${id}.truth.json`), JSON.stringify(truth, null, 2));
		manifest.push({ id, kind, seed, variant: variant.name, width: variant.width, height: variant.height });
	}
	await page.close();
}
await browser.close();
await writeFile(join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(`captured ${manifest.length} frames into ${OUT}`);
