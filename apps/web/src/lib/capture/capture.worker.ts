/// <reference lib="webworker" />
import { ChangeGate } from './gate.ts';
import { GRID_H, GRID_W, tileHashes, toGray } from './hash.ts';

export type WorkerIn =
	| { kind: 'frame'; bitmap: ImageBitmap; now: number; maxWidth: number }
	| { kind: 'invalidate' }
	| { kind: 'reset' };

export type WorkerOut =
	| { kind: 'frame'; blob: Blob; w: number; h: number; score: number; tiles: number[]; cpuMs: number }
	| { kind: 'pointer'; x: number; y: number; cpuMs: number }
	| { kind: 'idle'; cpuMs: number }
	| { kind: 'error'; message: string };

const gate = new ChangeGate();
const small = new OffscreenCanvas(GRID_W, GRID_H);
const smallCtx = small.getContext('2d', { willReadFrequently: true })!;

async function handle(msg: Extract<WorkerIn, { kind: 'frame' }>): Promise<WorkerOut> {
	const started = performance.now();
	const { bitmap } = msg;
	try {
		smallCtx.drawImage(bitmap, 0, 0, GRID_W, GRID_H);
		const gray = toGray(smallCtx.getImageData(0, 0, GRID_W, GRID_H).data);
		const decision = gate.push({ now: msg.now, gray, hashes: tileHashes(gray) });
		if (decision.kind === 'pointer') return { kind: 'pointer', x: decision.x, y: decision.y, cpuMs: performance.now() - started };
		if (decision.kind === 'wait') return { kind: 'idle', cpuMs: performance.now() - started };
		const scale = Math.min(1, msg.maxWidth / bitmap.width);
		const w = Math.round(bitmap.width * scale);
		const h = Math.round(bitmap.height * scale);
		const full = new OffscreenCanvas(w, h);
		full.getContext('2d')!.drawImage(bitmap, 0, 0, w, h);
		const blob = await full.convertToBlob({ type: 'image/webp', quality: 0.85 });
		return { kind: 'frame', blob, w, h, score: decision.score, tiles: decision.tiles, cpuMs: performance.now() - started };
	} finally {
		bitmap.close();
	}
}

self.onmessage = async (ev: MessageEvent<WorkerIn>) => {
	const msg = ev.data;
	if (msg.kind === 'invalidate') return gate.invalidate();
	if (msg.kind === 'reset') return gate.reset();
	try {
		self.postMessage(await handle(msg));
	} catch (err) {
		self.postMessage({ kind: 'error', message: err instanceof Error ? err.message : String(err) } satisfies WorkerOut);
	}
};
