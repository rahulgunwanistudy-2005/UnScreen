/** Grayscale grid and per-tile difference hashes used by the change gate. Pure functions. */

export const GRID_W = 320;
export const GRID_H = 180;
export const TILES_X = 16;
export const TILES_Y = 9;

/** RGBA pixels (already downscaled to GRID_W x GRID_H) -> luma bytes. */
export function toGray(rgba: Uint8ClampedArray, w = GRID_W, h = GRID_H): Uint8Array {
	const out = new Uint8Array(w * h);
	for (let i = 0, p = 0; i < out.length; i++, p += 4) {
		out[i] = (rgba[p] * 77 + rgba[p + 1] * 150 + rgba[p + 2] * 29) >> 8;
	}
	return out;
}

/**
 * dHash per tile: each tile's 20x20 cells are compared to their right-hand neighbour, giving
 * a 19-bit-per-row signature plus 4 bits of mean brightness. One bigint per tile.
 */
export function tileHashes(gray: Uint8Array, w = GRID_W, h = GRID_H): bigint[] {
	const tw = Math.floor(w / TILES_X);
	const th = Math.floor(h / TILES_Y);
	const hashes: bigint[] = [];
	for (let ty = 0; ty < TILES_Y; ty++) {
		for (let tx = 0; tx < TILES_X; tx++) {
			let hash = 0n;
			for (let y = 0; y < th; y++) {
				const row = (ty * th + y) * w + tx * tw;
				for (let x = 0; x < tw - 1; x++) {
					hash = (hash << 1n) | (gray[row + x] > gray[row + x + 1] + 2 ? 1n : 0n);
				}
			}
			// Also fold in mean brightness so flat colour changes (a filled cell) register.
			let sum = 0;
			for (let y = 0; y < th; y++) for (let x = 0; x < tw; x++) sum += gray[(ty * th + y) * w + tx * tw + x];
			hash = (hash << 4n) | BigInt(Math.floor(sum / (tw * th)) >> 4);
			hashes.push(hash);
		}
	}
	return hashes;
}

export function changedTiles(a: readonly bigint[], b: readonly bigint[]): number[] {
	const out: number[] = [];
	for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) out.push(i);
	return out;
}

export type Blob = { x0: number; y0: number; x1: number; y1: number; size: number };

/** Connected regions of changed pixels between two gray grids (4-connectivity). */
export function changedBlobs(a: Uint8Array, b: Uint8Array, w = GRID_W, h = GRID_H, delta = 24): Blob[] {
	const mask = new Uint8Array(w * h);
	for (let i = 0; i < mask.length; i++) mask[i] = Math.abs(a[i] - b[i]) > delta ? 1 : 0;
	const blobs: Blob[] = [];
	const stack: number[] = [];
	for (let start = 0; start < mask.length; start++) {
		if (mask[start] !== 1) continue;
		const blob: Blob = { x0: w, y0: h, x1: 0, y1: 0, size: 0 };
		mask[start] = 2;
		stack.push(start);
		while (stack.length) {
			const i = stack.pop()!;
			const x = i % w;
			const y = (i - x) / w;
			blob.size++;
			blob.x0 = Math.min(blob.x0, x);
			blob.y0 = Math.min(blob.y0, y);
			blob.x1 = Math.max(blob.x1, x);
			blob.y1 = Math.max(blob.y1, y);
			for (const n of [i - 1, i + 1, i - w, i + w]) {
				if (n < 0 || n >= mask.length || mask[n] !== 1) continue;
				if ((n === i - 1 && x === 0) || (n === i + 1 && x === w - 1)) continue;
				mask[n] = 2;
				stack.push(n);
			}
		}
		blobs.push(blob);
	}
	return blobs;
}
