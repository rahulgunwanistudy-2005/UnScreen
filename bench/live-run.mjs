// Live loop run: the real reader app, the real engine and the real Gemini API, watching a
// scripted fixture that edits itself. Measures change-detection precision and recall and
// change-to-announcement latency against the fixture's own ground truth.
//
// Usage: node live-run.mjs [--kind sheet|code] [--seed 3] [--edits 6] [--interval 60000] [--name live]
// Needs the web app on :5173 and the engine on :8787.
//
// Browser tab capture cannot start inside automation on macOS ("Could not start video
// source"), so getDisplayMedia is replaced by a canvas stream that receives real screenshots
// of the fixture tab every 400 ms. Everything after the stream is the shipped code path.
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const arg = (k, d) => {
	const i = process.argv.indexOf(`--${k}`);
	return i > 0 ? process.argv[i + 1] : d;
};
const KIND = arg('kind', 'sheet');
const SEED = Number(arg('seed', '3'));
const EDITS = Number(arg('edits', '6'));
const INTERVAL = Number(arg('interval', '60000'));
const NAME = arg('name', `live-${KIND}`);
const BASE = 'http://localhost:5173';
const GRACE_MS = Number(arg('grace', '240000'));

const norm = (s) => String(s ?? '').replace(/\s+/g, ' ').trim().toLowerCase();

function diffTruth(a, b) {
	const out = [];
	if (KIND === 'sheet') {
		const cols = b.sheet.columns;
		const before = new Map(a.sheet.rows.map((r) => [r[0], r]));
		for (const row of b.sheet.rows) {
			const prev = before.get(row[0]);
			if (!prev) {
				out.push({ kind: 'row_added', row: row[0] });
				continue;
			}
			row.forEach((v, j) => {
				if (prev[j] !== v) out.push({ kind: 'cell', row: row[0], col: cols[j], old: prev[j], new: v });
			});
		}
	} else {
		const before = a.code.lines.map((l) => l.text);
		const after = b.code.lines.map((l) => l.text);
		if (before.length !== after.length) out.push({ kind: 'lines', delta: after.length - before.length });
		else after.forEach((t, i) => t !== before[i] && out.push({ kind: 'line', n: i + 1, old: before[i], new: t }));
	}
	return out;
}

function matches(change, msg) {
	const t = norm(msg.text);
	if (change.kind === 'cell') return t.includes(norm(change.row)) && t.includes(norm(change.col));
	if (change.kind === 'row_added') return msg.kind === 'row_added' && t.includes(norm(change.row));
	if (change.kind === 'line') return t.includes(`line ${change.n}`);
	if (change.kind === 'lines') return ['lines_added', 'lines_removed', 'line', 'scroll'].includes(msg.kind);
	return false;
}

const browser = await chromium.launch();
const fixtureCtx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const appCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const fixture = await fixtureCtx.newPage();
const app = await appCtx.newPage();

await app.addInitScript(() => {
	navigator.mediaDevices.getDisplayMedia = async () => {
		const c = document.createElement('canvas');
		c.width = 1280;
		c.height = 720;
		const ctx = c.getContext('2d');
		window.__feed = async (b64) => {
			const img = new Image();
			img.src = `data:image/jpeg;base64,${b64}`;
			await img.decode();
			ctx.drawImage(img, 0, 0, c.width, c.height);
		};
		return c.captureStream(5);
	};
});

const t0 = Date.now();
const consoleLog = [];
app.on('console', (m) => consoleLog.push(`${m.type()}: ${m.text()}`));
app.on('pageerror', (e) => consoleLog.push(`pageerror: ${e.message}`));
const events = [];
const announces = [];
let snapshotAt = null;
app.on('websocket', (ws) => {
	ws.on('framereceived', (f) => {
		if (typeof f.payload !== 'string') return;
		const msg = JSON.parse(f.payload);
		const at = Date.now() - t0;
		if (msg.type === 'announce') announces.push({ at, ...msg });
		if (msg.type === 'snapshot' && snapshotAt === null) snapshotAt = at;
		if (msg.type === 'status' && msg.latency_ms) events.push({ at, stage: msg.stage, mode: msg.detail, latency_ms: msg.latency_ms });
		if (msg.type === 'error') events.push({ at, error: msg.code, message: msg.message });
	});
});
const spoken = [];
await app.exposeFunction('__spoken', (text) => spoken.push({ at: Date.now() - t0, text }));

await fixture.goto(`${BASE}/fixture/${KIND}?seed=${SEED}&mode=live&interval=${INTERVAL}`);
await fixture.waitForFunction(() => typeof window.__truth === 'function');
await app.goto(`${BASE}/app`, { waitUntil: 'networkidle' });
await app.waitForFunction(() => document.querySelector('#status-line') !== null);
await new Promise((r) => setTimeout(r, 1500));
await app.evaluate(() => {
	const live = document.querySelector('[role="status"][aria-live="polite"]');
	new MutationObserver(() => window.__spoken(live.textContent)).observe(live, { childList: true, characterData: true, subtree: true });
});

let feeding = true;
const feeder = (async () => {
	while (feeding) {
		const shot = await fixture.screenshot({ type: 'jpeg', quality: 90 });
		await app.evaluate((b64) => window.__feed?.(b64), shot.toString('base64'));
		await new Promise((r) => setTimeout(r, 400));
	}
})();

await app.getByRole('button', { name: 'Start reading the shared screen' }).click();
await new Promise((r) => setTimeout(r, 4000));
console.log('status after start:', await app.locator('#status-line').textContent());
if (consoleLog.length) console.log(consoleLog.join('\n'));

const truthLog = [];
let prev = await fixture.evaluate(() => window.__truth());
truthLog.push({ at: Date.now() - t0, edits: prev.edits });
const changes = [];
while (prev.edits < EDITS) {
	await new Promise((r) => setTimeout(r, 250));
	const cur = await fixture.evaluate(() => window.__truth());
	if (cur.edits !== prev.edits) {
		const at = Date.now() - t0;
		for (const c of diffTruth(prev, cur)) changes.push({ at, edit: cur.edits, ...c });
		truthLog.push({ at, edits: cur.edits });
		prev = cur;
	}
}
// Freeze the fixture so late announcements can be attributed, then wait for the engine.
await fixture.evaluate(() => {
	for (let i = 1; i < 99999; i++) clearInterval(i);
});
const lastEditAt = Date.now() - t0;
while (Date.now() - t0 - lastEditAt < GRACE_MS) {
	await new Promise((r) => setTimeout(r, 2000));
	const pending = changes.filter((c) => !announces.some((a) => a.at > c.at && matches(c, a)));
	if (pending.length === 0) break;
}
feeding = false;
await feeder;

const domRows = await app.evaluate(() => [...document.querySelectorAll('main table tbody tr')].map((tr) => [...tr.children].map((c) => c.textContent.trim())));
const finalTruth = await fixture.evaluate(() => window.__truth());

const rows = changes.map((c) => {
	const hit = announces.find((a) => a.at > c.at && matches(c, a));
	return {
		...c,
		announced: !!hit,
		unclear: hit ? hit.kind === 'uncertain' : null,
		latency_ms: hit ? hit.at - c.at : null,
		text: hit?.text ?? null
	};
});
const contentAnnounces = announces.filter((a) => a.kind !== 'content_type');
const truePositives = contentAnnounces.filter((a) => changes.some((c) => a.at > c.at && matches(c, a)));
const lat = rows.filter((r) => r.latency_ms !== null).map((r) => r.latency_ms).sort((a, b) => a - b);
const pick = (q) => (lat.length ? lat[Math.min(lat.length - 1, Math.round(q * (lat.length - 1)))] : null);
let finalCellsMatch = null;
if (KIND === 'sheet') {
	const want = finalTruth.sheet.rows.map((r) => r.map(norm));
	const got = domRows.map((r) => r.map((v) => norm(v.replace(/\s*\(unclear\)$/, ''))));
	const total = want.flat().length;
	let ok = 0;
	want.forEach((r, i) => r.forEach((v, j) => got[i]?.[j] === v && ok++));
	finalCellsMatch = { ok, total };
}

const report = {
	name: NAME,
	run_at: new Date().toISOString(),
	kind: KIND,
	seed: SEED,
	edit_interval_ms: INTERVAL,
	first_snapshot_ms: snapshotAt,
	truth_changes: rows.length,
	recall: rows.length ? rows.filter((r) => r.announced).length / rows.length : null,
	precision: contentAnnounces.length ? truePositives.length / contentAnnounces.length : null,
	change_to_announce_ms: { p50: pick(0.5), p95: pick(0.95), n: lat.length },
	final_dom_vs_truth: finalCellsMatch,
	changes: rows,
	announces,
	spoken,
	engine_events: events,
	console: consoleLog
};
await mkdir(join(import.meta.dirname, 'results'), { recursive: true });
const out = join(import.meta.dirname, 'results', `${new Date().toISOString().slice(0, 10)}-${NAME}.json`);
await writeFile(out, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ ...report, changes: undefined, announces: undefined, spoken: undefined, engine_events: undefined }, null, 2));
console.log(`wrote ${out}`);
await browser.close();
