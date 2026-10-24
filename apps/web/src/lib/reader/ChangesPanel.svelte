<script lang="ts">
	import Icon from '#lib/site/Icon.svelte';
	import type { HistoryEntry } from '#lib/doc/store.svelte.ts';
	import { tick } from 'svelte';
	import DocView from './DocView.svelte';

	let { history }: { history: HistoryEntry[] } = $props();

	let selected = $state<number | null>(null);
	let heading: HTMLHeadingElement;
	let viewHeading = $state<HTMLHeadingElement>();
	let origin: HTMLButtonElement | null = null;
	const viewing = $derived(selected === null ? null : (history.find((h) => h.version === selected) ?? null));
	const time = (at: number) => new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

	export function focus() {
		heading.focus();
	}

	async function open(version: number, button: HTMLButtonElement) {
		origin = button;
		selected = version;
		await tick();
		viewHeading?.focus();
	}

	async function close() {
		selected = null;
		await tick();
		if (origin?.isConnected) origin.focus();
		else heading.focus();
	}
</script>

<section aria-labelledby="changes-h">
	<h2 id="changes-h" tabindex="-1" bind:this={heading}><Icon name="history" size={19} /> Changes</h2>
	{#if history.length === 0}
		<p>Each change to the shared screen is listed here, newest first. Choose one to read that version.</p>
	{:else}
		<ol reversed class="timeline">
			{#each history as h (h.version)}
				<li>
					<button type="button" aria-current={selected === h.version ? 'true' : undefined} onclick={(e) => open(h.version, e.currentTarget)}>
						<span class="when">Version {h.version}, {time(h.at)}</span>
						<span class="what">{h.summary}</span>
					</button>
				</li>
			{/each}
		</ol>
	{/if}
</section>

{#if viewing}
	<section class="past" aria-labelledby="past-h">
		<h2 id="past-h" tabindex="-1" bind:this={viewHeading}>Version {viewing.version}, {time(viewing.at)}</h2>
		<p>This is an earlier version. The live screen keeps updating above.</p>
		<button class="button quiet" type="button" onclick={close}>Close this version</button>
		<div class="past-doc"><DocView doc={viewing.doc} idPrefix="v{viewing.version}-" /></div>
	</section>
{/if}

<style>
	.timeline {
		list-style: none;
		margin: 0;
		padding: 0;
		max-height: 28rem;
		overflow-y: auto;
	}
	.timeline button {
		display: grid;
		width: 100%;
		text-align: start;
		background: none;
		border: 0;
		border-bottom: 1px solid var(--rule);
		padding: 0.6em 0.2em;
		cursor: pointer;
	}
	.timeline button:hover .what {
		text-decoration: underline;
	}
	.timeline button[aria-current='true'] {
		background: var(--signal);
		color: var(--on-signal);
	}
	.when {
		font-size: var(--s-1);
		color: inherit;
		opacity: 0.85;
	}
	.past-doc {
		margin-top: 1rem;
		overflow-x: auto;
	}
</style>
