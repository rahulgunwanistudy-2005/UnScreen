import { changedBlobs, changedTiles, type Blob, GRID_H, GRID_W, TILES_X, TILES_Y } from './hash.ts';

export type GateConfig = {
	/** Share of tiles that must differ from the last sent frame. */
	threshold: number;
	/** The frame must be unchanged for this long before it is sent. */
	stableMs: number;
	/** Largest blob, in grid cells per side, that can be a mouse pointer. */
	pointerMax: number;
};

export const DEFAULT_GATE: GateConfig = { threshold: 1 / (TILES_X * TILES_Y), stableMs: 300, pointerMax: 7 };

export type GateInput = { now: number; hashes: bigint[]; gray: Uint8Array };

export type GateDecision =
	| { kind: 'send'; score: number; tiles: number[] }
	| { kind: 'pointer'; x: number; y: number }
	| { kind: 'wait' };

type Seen = { hashes: bigint[]; gray: Uint8Array };

function isPointerSized(b: Blob, max: number): boolean {
	return b.x1 - b.x0 < max && b.y1 - b.y0 < max + 1;
}

function contrast(gray: Uint8Array, blob: Blob): number {
	let sum = 0;
	for (let y = Math.max(0, blob.y0 - 1); y < Math.min(GRID_H - 1, blob.y1 + 2); y++) {
		for (let x = Math.max(0, blob.x0 - 1); x < Math.min(GRID_W - 1, blob.x1 + 2); x++) {
			const i = y * GRID_W + x;
			sum += Math.abs(gray[i] - gray[i + 1]) + Math.abs(gray[i] - gray[i + GRID_W]);
		}
	}
	return sum;
}

/**
 * Decides when a captured frame is worth sending: it must differ from the last frame sent
 * and have been still for `stableMs` (no mid-scroll or mid-animation frames). A move of a
 * small blob from one place to another, with nothing else changing, is the presenter's
 * pointer and is reported instead of sent.
 */
export class ChangeGate {
	private sent: Seen | null = null;
	private prev: Seen | null = null;
	private stableSince = 0;

	constructor(private config: GateConfig = DEFAULT_GATE) {}

	reset(): void {
		this.sent = null;
		this.prev = null;
	}

	/** Force the next stable frame to be sent (e.g. after a reconnect). */
	invalidate(): void {
		this.sent = null;
	}

	push(input: GateInput): GateDecision {
		const prev = this.prev;
		this.prev = { hashes: input.hashes, gray: input.gray };
		if (!prev) {
			this.stableSince = input.now;
			return { kind: 'wait' };
		}
		const moving = changedTiles(prev.hashes, input.hashes);
		if (moving.length > 0) {
			const pointer = this.pointerMove(prev.gray, input.gray);
			if (pointer) {
				if (this.sent) this.sent = { hashes: input.hashes, gray: input.gray };
				return { kind: 'pointer', ...pointer };
			}
			this.stableSince = input.now;
			return { kind: 'wait' };
		}
		if (input.now - this.stableSince < this.config.stableMs) return { kind: 'wait' };
		if (!this.sent) {
			this.sent = { hashes: input.hashes, gray: input.gray };
			return { kind: 'send', score: 1, tiles: [] };
		}
		const tiles = changedTiles(this.sent.hashes, input.hashes);
		const score = tiles.length / (TILES_X * TILES_Y);
		if (tiles.length === 0 || score < this.config.threshold) return { kind: 'wait' };
		this.sent = { hashes: input.hashes, gray: input.gray };
		return { kind: 'send', score, tiles };
	}

	private pointerMove(a: Uint8Array, b: Uint8Array): { x: number; y: number } | null {
		const blobs = changedBlobs(a, b).filter((blob) => blob.size > 1);
		if (blobs.length !== 2 || !blobs.every((blob) => isPointerSized(blob, this.config.pointerMax))) return null;
		const centres = blobs.map((blob) => ({ x: (blob.x0 + blob.x1 + 1) / 2, y: (blob.y0 + blob.y1 + 1) / 2 }));
		// Two nearby small blobs are more likely two edited characters than a pointer jump.
		if (Math.hypot(centres[0].x - centres[1].x, centres[0].y - centres[1].y) < 2 * this.config.pointerMax) return null;
		// A cursor appears at one blob and disappears at the other. Scan order is
		// spatial, not temporal; choosing the last blob reports the old cursor on
		// an upward jump. Require an added edge and a removed edge, otherwise abstain.
		const delta = blobs.map((blob) => contrast(b, blob) - contrast(a, blob));
		const index = delta[0] > delta[1] ? 0 : 1;
		if (delta[index] <= 0 || delta[1 - index] >= 0) return null;
		const next = blobs[index];
		// Use the arrow's leading corner, close to its hotspot, rather than its centre.
		return { x: Math.round(((next.x0 + 0.5) / GRID_W) * 1000), y: Math.round(((next.y0 + 0.5) / GRID_H) * 1000) };
	}
}
