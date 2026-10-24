/** Ground truth exposed by fixture pages as `window.__truth()`. Boxes are 0..1000 of the viewport. */
export type TruthBox = { x0: number; y0: number; x1: number; y1: number };

export type SheetTruth = {
	sheet_name: string;
	columns: string[];
	rows: string[][];
};

export type CodeTruth = {
	file_name: string;
	language: string;
	lines: { n: number; text: string }[];
	cursor_line: number;
};

export type BlockTruth = { kind: string; level: number | null; text: string };

export type FixtureTruth = {
	seed: number;
	content_type: 'sheet' | 'code' | 'slide' | 'doc';
	title: string;
	sheet?: SheetTruth;
	code?: CodeTruth;
	blocks?: BlockTruth[];
	content_bbox: TruthBox;
	/** Keyed by `data-truth` attribute: `h{c}` header, `r{r}c{c}` cell, `l{n}` code line, `b{i}` block. */
	boxes: Record<string, TruthBox>;
	pointer: { x: number; y: number; target: string | null } | null;
	edits: number;
};

export function boxOf(el: Element): TruthBox {
	const r = el.getBoundingClientRect();
	const w = window.innerWidth;
	const h = window.innerHeight;
	const clamp = (v: number) => Math.max(0, Math.min(1000, Math.round(v)));
	return {
		x0: clamp((r.left / w) * 1000),
		y0: clamp((r.top / h) * 1000),
		x1: clamp((r.right / w) * 1000),
		y1: clamp((r.bottom / h) * 1000)
	};
}

export function collectBoxes(root: ParentNode): Record<string, TruthBox> {
	const boxes: Record<string, TruthBox> = {};
	for (const el of root.querySelectorAll('[data-truth]')) {
		const key = el.getAttribute('data-truth');
		if (key) boxes[key] = boxOf(el);
	}
	return boxes;
}

export function targetAt(boxes: Record<string, TruthBox>, x: number, y: number): string | null {
	for (const [key, b] of Object.entries(boxes)) {
		if (key === 'content') continue;
		if (x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1) return key;
	}
	return null;
}

declare global {
	interface Window {
		__truth?: () => FixtureTruth;
		/** Advance the real fixture DOM once, for a controlled live-model measurement. */
		__advance?: () => void;
		__movePointer?: () => void;
	}
}
