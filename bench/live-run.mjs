// Live loop run: the real reader app, the real engine and the real Gemini API, watching a
// scripted fixture that edits itself. Measures change-detection precision and recall and
// change-to-announcement latency against the fixture's own ground truth.
//
// Usage: node live-run.mjs [--kind sheet|code] [--seed 3] [--edits 6] [--interval 25000] [--name live]
// Needs the web app on :5173 and the engine on :8787.
//
// Browser tab capture cannot start inside automation on macOS ("Could not start video
// source"), so getDisplayMedia is replaced by a canvas stream that receives real screenshots
// of the fixture tab every 400 ms. Everything after the stream is the shipped code path.
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { norm, matches, scoreChanges } from './live-score.mjs';

const arg = (k, d) => {
	const i = process.argv.indexOf(`--${k}`);
	return i > 0 ? process.argv[i + 1] : d;
};
const KIND = arg('kind', 'sheet');
const SEED = Number(arg('seed', '3'));
const EDITS = Number(arg('edits', '6'));
const INTERVAL = Number(arg('interval', '25000'));
const NAME = arg('name', `live-${KIND}`);
const BASE = arg('base', 'http://localhost:5173');
const ENGINE = arg('engine', 'http://localhost:8787');
const GRACE_MS = Number(arg('grace', '120000'));
if (!['sheet', 'code'].includes(KIND) || !Number.isInteger(EDITS) || EDITS < 6 || INTERVAL < 20000 || INTERVAL > 30000) {
	throw new Error('Use sheet or code, at least 6 edits, and an interval from 20000 to 30000 ms.');
}

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
		for (const row of a.sheet.rows) if (!b.sheet.rows.some((r) => r[0] === row[0])) out.push({ kind: 'row_removed', row: row[0] });
	} else {
		const before = a.code.lines.map((l) => l.text);
		const after = b.code.lines.map((l) => l.text);
		if (before.length !== after.length) out.push({ kind: 'lines', delta: after.length - before.length });
		else after.forEach((t, i) => t !== before[i] && out.push({ kind: 'line', n: i + 1, old: before[i], new: t }));
	}
	return out;
}

const healthResponse = await fetch(`${ENGINE}/healthz`);
if (!healthResponse.ok) throw new Error('The engine health check failed.');
const health = await healthResponse.json();
if (health.llm_mode !== 'live') throw new Error('Live measurements require UNSCREEN_LLM_MODE=live; scripted/replayed results are refused.');
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
const messages = [];
const probes = [];
let snapshotAt = null;
app.on('websocket', (ws) => {
	ws.on('framereceived', (f) => {
		if (typeof f.payload !== 'string') return;
		const msg = JSON.parse(f.payload);
		const at = Date.now() - t0;
		messages.push({ at, message: msg });
		if (msg.type === 'announce') announces.push({ at, ...msg });
		if (msg.type === 'snapshot' && snapshotAt === null) snapshotAt = at;
		if (msg.type === 'status' && msg.latency_ms) events.push({ at, stage: msg.stage, mode: msg.detail, latency_ms: msg.latency_ms });
		if (msg.type === 'error') events.push({ at, error: msg.code, message: msg.message });
	});
});
const spoken = [];
await app.exposeFunction('__spoken', (text) => spoken.push({ at: Date.now() - t0, text }));

await fixture.goto(`${BASE}/fixture/${KIND}?seed=${SEED}&mode=static&cursor=on`);
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
const initialDeadline = Date.now() + 180000;
while (snapshotAt === null && Date.now() < initialDeadline && !events.some((e) => e.error === 'engine_busy')) {
	await new Promise((r) => setTimeout(r, 250));
}
console.log('status after start:', await app.locator('#status-line').textContent());
if (consoleLog.length) console.log(consoleLog.join('\n'));

const truthLog = [];
let prev = await fixture.evaluate(() => window.__truth());
truthLog.push({ at: Date.now() - t0, edits: prev.edits });
const changes = [];
let focusTarget = null;
if (snapshotAt !== null) {
	const target = app.locator(KIND === 'sheet' ? 'main table tbody tr:first-child > :nth-child(2)' : 'main .line').first();
	if (await target.count()) { await target.focus(); focusTarget = await target.elementHandle(); }
}
while (snapshotAt !== null && prev.edits < EDITS) {
	await new Promise((r) => setTimeout(r, INTERVAL));
	const editAt = Date.now() - t0;
	await fixture.evaluate(() => window.__advance());
	await fixture.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
	const cur = await fixture.evaluate(() => window.__truth());
	if (cur.edits !== prev.edits) {
		const at = editAt;
		for (const c of diffTruth(prev, cur)) changes.push({ at, edit: cur.edits, ...c });
		truthLog.push({ at, edits: cur.edits });
		prev = cur;
	}
}
// Controlled DOM edits are now finished. Allow the final frame to settle.
const lastEditAt = Date.now() - t0;
while (Date.now() - t0 - lastEditAt < GRACE_MS) {
	await new Promise((r) => setTimeout(r, 2000));
	const pending = changes.filter((c) => !announces.some((a) => a.at > c.at && matches(c, a)));
	if (pending.length === 0) break;
}
const focusValidation = focusTarget ? await focusTarget.evaluate((el) => ({ original_connected: el.isConnected, same_active_element: document.activeElement === el })) : null;

if (snapshotAt !== null) {
	await fixture.evaluate(() => window.__movePointer?.());
	await new Promise((r) => setTimeout(r, 2000));
	const pointer = await fixture.evaluate(() => window.__truth().pointer);
	if (pointer) {
		await app.getByRole('button', { name: 'What is the pointer on?' }).click();
		await new Promise((r) => setTimeout(r, 1000));
		probes.push({ kind: 'pointer', truth: pointer, result: messages.findLast((e) => e.message.type === 'pointer_target')?.message ?? null });
	}
	feeding = false;
	await feeder;
	const truth = await fixture.evaluate(() => window.__truth());
	const question = KIND === 'sheet' ? `What is ${truth.sheet.rows[0][0]}'s ${truth.sheet.columns[2]}? Cite the cell.` : 'What does line 2 say? Cite the line.';
	await app.getByLabel('Question', { exact: true }).fill(question);
	await app.getByRole('button', { name: 'Ask', exact: true }).click();
	const deadline = Date.now() + 120000;
	while (!messages.some((e) => e.message.type === 'answer') && Date.now() < deadline && !events.some((e) => e.error === 'engine_busy')) await new Promise((r) => setTimeout(r, 250));
	probes.push({ kind: 'ask', question, expected: KIND === 'sheet' ? truth.sheet.rows[0][2] : truth.code.lines[1]?.text, result: messages.findLast((e) => e.message.type === 'answer')?.message ?? null });
}
feeding = false;
await feeder;

const domRows = await app.evaluate(() => [...document.querySelectorAll('main table tbody tr')].map((tr) => [...tr.children].map((c) => c.textContent.trim())));
const finalTruth = await fixture.evaluate(() => window.__truth());

const scored = scoreChanges(changes, announces, spoken);
const rows = scored.rows;
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
	models: health.models,
	cross_check: health.cross_check,
	llm_mode: health.llm_mode,
	edit_interval_ms: INTERVAL,
	first_snapshot_ms: snapshotAt,
	truth_changes: rows.length,
	measurement_version: 3,
	note: 'Real fixture screenshots through a canvas capture stream; this is not a Google Meet or human screen-reader pass. Latency ends at the polite live region, not an audio device.',
	recall: scored.recall,
	spoken_recall: scored.spoken_recall,
	precision: scored.precision,
	change_to_announce_ms: { p50: pick(0.5), p95: pick(0.95), n: lat.length },
	final_dom_vs_truth: finalCellsMatch,
	changes: rows,
	announces,
	spoken,
	engine_events: events,
	probes,
	focus_validation: focusValidation,
	messages,
	console: consoleLog
};
await mkdir(join(import.meta.dirname, 'results'), { recursive: true });
const out = join(import.meta.dirname, 'results', `${new Date().toISOString().slice(0, 10)}-${NAME}.json`);
await writeFile(out, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ ...report, changes: undefined, announces: undefined, spoken: undefined, engine_events: undefined, messages: undefined, console: undefined }, null, 2));
console.log(`wrote ${out}`);
await browser.close();
