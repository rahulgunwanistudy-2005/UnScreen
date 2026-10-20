<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import CodeView from '#lib/fixture/CodeView.svelte';
	import FakeCursor from '#lib/fixture/FakeCursor.svelte';
	import MeetingFrame from '#lib/fixture/MeetingFrame.svelte';
	import { applyCodeEdit, generateCode, nextCodeEdit } from '#lib/fixture/code.ts';
	import { readParams } from '#lib/fixture/params.ts';
	import { createRng } from '#lib/fixture/rng.ts';
	import { collectBoxes, targetAt, type FixtureTruth } from '#lib/fixture/truth.ts';

	const params = readParams(page.url);
	const MAX_LINES = 40;
	let code = $state(generateCode(params.seed));
	let edits = $state(0);
	let cursor = $state({ x: 40, y: 40 });
	let root: HTMLElement;

	function truth(): FixtureTruth {
		const boxes = collectBoxes(root);
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
			content_type: 'code',
			title: code.fileName,
			code: {
				file_name: code.fileName,
				language: code.language,
				lines: code.lines.slice(0, MAX_LINES).map((text, i) => ({ n: i + 1, text })),
				cursor_line: code.cursor.line + 1
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
		const rng = createRng(params.seed * 104729);
		const timer = setInterval(() => {
			applyCodeEdit(code, nextCodeEdit(code, rng));
			edits += 1;
		}, params.intervalMs);
		const mover = setInterval(() => {
			cursor = { x: 10 + rng.next() * 50, y: 15 + rng.next() * 65 };
		}, Math.max(1500, params.intervalMs / 2.5));
		return () => {
			clearInterval(timer);
			clearInterval(mover);
		};
	});
</script>

<svelte:head><title>Code editor test fixture | UnScreen</title></svelte:head>

<div bind:this={root}>
	<MeetingFrame enabled={params.frame === 'meet'}>
		<CodeView {code} maxLines={MAX_LINES} />
		{#if params.cursor}<FakeCursor x={cursor.x} y={cursor.y} />{/if}
	</MeetingFrame>
</div>
