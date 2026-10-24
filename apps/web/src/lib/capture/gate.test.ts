import { describe, expect, it } from 'vitest';
import { ChangeGate } from './gate.ts';
import { changedBlobs, changedTiles, GRID_H, GRID_W, tileHashes } from './hash.ts';

function canvas(): Uint8Array {
	return new Uint8Array(GRID_W * GRID_H).fill(240);
}
function rect(g: Uint8Array, x: number, y: number, w: number, h: number, v = 20): Uint8Array {
	const out = g.slice();
	for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) out[j * GRID_W + i] = v;
	return out;
}
function frame(gray: Uint8Array, now: number) {
	return { now, gray, hashes: tileHashes(gray) };
}

describe('tile hashes', () => {
	it('change only in the touched tile', () => {
		const a = canvas();
		const b = rect(a, 25, 25, 6, 3);
		const tiles = changedTiles(tileHashes(a), tileHashes(b));
		expect(tiles).toEqual([1 * 16 + 1]);
	});

	it('finds separate blobs', () => {
		const a = canvas();
		const b = rect(rect(a, 10, 10, 3, 4), 200, 100, 3, 4);
		expect(changedBlobs(a, b)).toHaveLength(2);
	});
});

describe('ChangeGate', () => {
	it('sends the first stable frame, then only stable changes', () => {
		const gate = new ChangeGate();
		const a = canvas();
		expect(gate.push(frame(a, 0)).kind).toBe('wait');
		expect(gate.push(frame(a, 500)).kind).toBe('send');
		expect(gate.push(frame(a, 1000)).kind).toBe('wait');
		const b = rect(a, 100, 60, 12, 4);
		expect(gate.push(frame(b, 1500)).kind).toBe('wait');
		const sent = gate.push(frame(b, 2000));
		expect(sent.kind).toBe('send');
	});

	it('never sends mid-scroll frames', () => {
		const gate = new ChangeGate();
		const a = canvas();
		gate.push(frame(a, 0));
		gate.push(frame(a, 500));
		for (let t = 1; t <= 4; t++) expect(gate.push(frame(rect(a, 0, t * 20, GRID_W, 6), 500 + t * 100)).kind).toBe('wait');
	});

	it('reports a pointer jump instead of sending', () => {
		const gate = new ChangeGate();
		const a = rect(canvas(), 40, 40, 3, 4);
		gate.push(frame(a, 0));
		gate.push(frame(a, 500));
		const moved = rect(canvas(), 200, 120, 3, 4);
		const d = gate.push(frame(moved, 1000));
		expect(d.kind).toBe('pointer');
		if (d.kind === 'pointer') {
			expect(Math.abs(d.x - Math.round((201.5 / GRID_W) * 1000))).toBeLessThan(10);
		}
		expect(gate.push(frame(moved, 1500)).kind).toBe('wait');
	});

	it('treats two nearby small changes as content, not a pointer', () => {
		const gate = new ChangeGate();
		const a = canvas();
		gate.push(frame(a, 0));
		gate.push(frame(a, 500));
		const b = rect(rect(a, 100, 60, 2, 3), 106, 60, 2, 3);
		expect(gate.push(frame(b, 1000)).kind).toBe('wait');
		expect(gate.push(frame(b, 1500)).kind).toBe('send');
	});

	it('tracks an upward first jump to the new cursor rather than its old location', () => {
		const gate = new ChangeGate();
		const old = rect(canvas(), 200, 120, 3, 4);
		gate.push(frame(old, 0)); gate.push(frame(old, 500));
		const moved = gate.push(frame(rect(canvas(), 40, 40, 3, 4), 1000));
		expect(moved.kind).toBe('pointer');
		if (moved.kind === 'pointer') { expect(moved.x).toBeLessThan(150); expect(moved.y).toBeLessThan(250); }
	});

	it('does not guess a pointer when two distant content marks appear', () => {
		const gate = new ChangeGate(); const old = canvas();
		gate.push(frame(old, 0)); gate.push(frame(old, 500));
		const next = rect(rect(old, 40, 40, 3, 4), 200, 120, 3, 4);
		expect(gate.push(frame(next, 1000)).kind).toBe('wait');
		expect(gate.push(frame(next, 1500)).kind).toBe('send');
	});
});
