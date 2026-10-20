<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import FakeCursor from '#lib/fixture/FakeCursor.svelte';
	import MeetingFrame from '#lib/fixture/MeetingFrame.svelte';
	import SheetView from '#lib/fixture/SheetView.svelte';
	import { readParams } from '#lib/fixture/params.ts';
	import { createRng } from '#lib/fixture/rng.ts';
	import { applySheetEdit, generateSheet, nextSheetEdits } from '#lib/fixture/sheet.ts';
	import { collectBoxes, targetAt, type FixtureTruth } from '#lib/fixture/truth.ts';

	const params = readParams(page.url);
	const MAX_ROWS = 14;
	let sheet = $state(generateSheet(params.seed, { rows: params.rows, cols: params.cols }));
	let firstRow = $state(0);
	let edits = $state(0);
	let selected = $state<{ row: number; col: number } | null>(null);
	let cursor = $state({ x: 46, y: 38 });
	let root: HTMLElement;

	function truth(): FixtureTruth {
		const boxes = collectBoxes(root);
		const visible = sheet.rows.slice(firstRow, firstRow + MAX_ROWS);
		const cursorEl = root.querySelector('svg.cursor');
		let pointer: FixtureTruth['pointer'] = null;
		if (params.cursor && cursorEl) {
			const r = cursorEl.getBoundingClientRect();
			const x = Math.round(((r.left + 2) / window.innerWidth) * 1000);
			const y = Math.round(((r.top + 2) / window.innerHeight) * 1000);
			pointer = { x, y, target: targetAt(boxes, x, y) };
		}
		return {
			seed: params.seed,
			content_type: 'sheet',
			title: sheet.title,
			sheet: {
				sheet_name: sheet.sheetName,
				columns: sheet.columns.map((c) => c.header),
				rows: visible.map((r) => [...r])
			},
			content_bbox: boxes.content,
			boxes,
			pointer,
			edits
		};
	}

	onMount(() => {
		window.__truth = truth;
		if (!params.live) return;
		const rng = createRng(params.seed * 7919);
		const timer = setInterval(() => {
			for (const edit of nextSheetEdits(sheet, rng)) {
				applySheetEdit(sheet, edit);
				if (edit.kind === 'cell') selected = { row: edit.row, col: edit.col };
				if (edit.kind === 'add_row' && sheet.rows.length > MAX_ROWS && rng.chance(0.5)) firstRow += 1;
			}
			edits += 1;
		}, params.intervalMs);
		const mover = setInterval(() => {
			cursor = { x: 8 + rng.next() * 70, y: 18 + rng.next() * 60 };
		}, Math.max(1500, params.intervalMs / 2.5));
		return () => {
			clearInterval(timer);
			clearInterval(mover);
		};
	});
</script>

<svelte:head><title>Spreadsheet test fixture | UnScreen</title></svelte:head>

<div bind:this={root}>
	<MeetingFrame enabled={params.frame === 'meet'}>
		<SheetView {sheet} {firstRow} maxRows={MAX_ROWS} {selected} />
		{#if params.cursor}<FakeCursor x={cursor.x} y={cursor.y} />{/if}
	</MeetingFrame>
</div>
