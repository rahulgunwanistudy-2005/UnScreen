// Package only actual server messages from a successful live-model report. No frames.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, basename } from 'node:path';
const source = process.argv[2];
if (!source) throw new Error('Pass a genuine bench/results live-run JSON file.');
const data = JSON.parse(await readFile(source, 'utf8'));
if (data.llm_mode !== 'live' || data.first_snapshot_ms === null || !data.messages?.length || data.kind !== 'sheet') {
	throw new Error('A successful real-model sheet run with recorded messages is required.');
}
const first = data.messages.findIndex((e) => e.message.type === 'snapshot');
if (first < 0 || !data.messages.some((e) => e.message.type === 'patch')) throw new Error('Recording needs a real snapshot and edits.');
const start = data.messages[first].at;
const events = data.messages.slice(first).map((e) => ({ at: e.at - start, message: e.message }));
const root = join(import.meta.dirname, '..', 'apps', 'web');
const target = join(root, 'static', 'recordings');
await mkdir(target, { recursive: true });
const pack = { schema_version: 1, source: `bench/results/${basename(source)}`, recorded_at: data.run_at, playback_rate: 2, models: data.models, events };
await writeFile(join(target, 'session.json'), JSON.stringify(pack));
await writeFile(join(root, 'src', 'lib', 'recording', 'catalog.json'), JSON.stringify({ available: true, title: 'Recorded real-model spreadsheet session', recorded_at: data.run_at, source: pack.source, playback_rate: 2 }, null, 2) + '\n');
console.log(`Packaged ${events.length} actual messages; no screenshots or API credentials included.`);
