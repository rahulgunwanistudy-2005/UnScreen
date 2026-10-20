<script lang="ts">
	import type { Block } from '@unscreen/schema';

	let {
		blocks,
		changed = {},
		idPrefix = ''
	}: { blocks: Block[]; changed?: Record<string, number>; idPrefix?: string } = $props();

	type Group = { id: string; list: boolean; items: Block[] };

	const groups = $derived.by(() => {
		const out: Group[] = [];
		for (const b of blocks) {
			const last = out[out.length - 1];
			if (b.kind === 'list_item' && last?.list) last.items.push(b);
			else out.push({ id: `g-${b.id}`, list: b.kind === 'list_item', items: [b] });
		}
		return out;
	});

	// The page's h1 is the shared title, so slide headings start at h2.
	const tag = (b: Block) => `h${Math.min(6, Math.max(2, (b.level ?? 1) + 1))}`;
</script>

{#snippet text(b: Block)}
	{#if b.unreadable}<em>unreadable</em>{:else}{b.text}{#if b.uncertain}<em> (unclear)</em>{/if}{/if}
{/snippet}

<div class="blocks">
	{#each groups as g (g.id)}
		{#if g.list}
			<ul>
				{#each g.items as b (b.id)}
					<li id="{idPrefix}{b.id}" data-ref={b.id} tabindex="-1" class:fresh={changed[b.id] !== undefined}>
						{@render text(b)}
					</li>
				{/each}
			</ul>
		{:else}
			{@const b = g.items[0]}
			{#if b.kind === 'heading'}
				<svelte:element
					this={tag(b)}
					id="{idPrefix}{b.id}"
					data-ref={b.id}
					tabindex="-1"
					class:fresh={changed[b.id] !== undefined}>{@render text(b)}</svelte:element
				>
			{:else if b.kind === 'figure'}
				<p id="{idPrefix}{b.id}" data-ref={b.id} tabindex="-1" class="figure" class:fresh={changed[b.id] !== undefined}>
					Picture: {@render text(b)}
				</p>
			{:else}
				<p id="{idPrefix}{b.id}" data-ref={b.id} tabindex="-1" class:fresh={changed[b.id] !== undefined}>
					{@render text(b)}
				</p>
			{/if}
		{/if}
	{/each}
</div>

<style>
	.blocks {
		max-width: var(--measure);
	}
	.fresh {
		background: var(--signal);
		color: var(--on-signal);
	}
	.figure {
		font-style: italic;
	}
	ul {
		padding-left: 1.2em;
	}
	li {
		margin-bottom: 0.3em;
	}
</style>
