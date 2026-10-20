<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import MeetingFrame from '#lib/fixture/MeetingFrame.svelte';
	import SlideView from '#lib/fixture/SlideView.svelte';
	import { readParams } from '#lib/fixture/params.ts';
	import { generateSlide } from '#lib/fixture/slide.ts';
	import { collectBoxes, type FixtureTruth } from '#lib/fixture/truth.ts';

	const params = readParams(page.url);
	const slide = generateSlide(params.seed);
	let root: HTMLElement;

	onMount(() => {
		window.__truth = (): FixtureTruth => {
			const boxes = collectBoxes(root);
			return {
				seed: params.seed,
				content_type: slide.kind,
				title: slide.title,
				blocks: slide.blocks.map((b) => ({ ...b })),
				content_bbox: boxes.content,
				boxes,
				pointer: null,
				edits: 0
			};
		};
	});
</script>

<svelte:head><title>Slide test fixture | UnScreen</title></svelte:head>

<div bind:this={root}>
	<MeetingFrame enabled={params.frame === 'meet'}>
		<SlideView {slide} />
	</MeetingFrame>
</div>
