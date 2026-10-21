<script lang="ts">
	import type { Document, PatchOp } from '@unscreen/schema';
	import { onMount } from 'svelte';
	import { DocStore } from '#lib/doc/store.svelte.ts';
	import DocView from '#lib/reader/DocView.svelte';

	// Test harness: renders the real reader components and lets tests push snapshots and patches.
	const store = new DocStore();

	onMount(() => {
		const w = window as unknown as Record<string, unknown>;
		w.__snapshot = (doc: Document) => store.snapshot({ type: 'snapshot', version: doc.version, doc });
		w.__patch = (version: number, base: number, ops: PatchOp[]) => store.patch({ type: 'patch', version, base, ops });
		w.__ready = true;
	});
</script>

<svelte:head><title>Reader test harness | UnScreen</title></svelte:head>

<main style="padding: 1rem; overflow: auto; height: 100vh; box-sizing: border-box">
	<h1>Reader test harness</h1>
	{#if store.doc}<DocView doc={store.doc} />{/if}
</main>
