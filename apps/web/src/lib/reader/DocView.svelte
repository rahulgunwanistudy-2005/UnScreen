<script lang="ts">
	import type { Document } from '@unscreen/schema';
	import BlockList from './BlockList.svelte';
	import CodeLines from './CodeLines.svelte';
	import SheetTable from './SheetTable.svelte';

	let {
		doc,
		changed = {},
		idPrefix = ''
	}: { doc: Document; changed?: Record<string, number>; idPrefix?: string } = $props();
</script>

{#if doc.content_type === 'sheet' && doc.sheet}
	<SheetTable sheet={doc.sheet} title={doc.title} {changed} {idPrefix} />
{:else if doc.content_type === 'code' && doc.code}
	<CodeLines code={doc.code} title={doc.title} {changed} {idPrefix} />
{:else if doc.blocks && doc.blocks.length > 0}
	<BlockList blocks={doc.blocks} {changed} {idPrefix} />
{:else}
	<p>Nothing readable is on the shared screen right now.</p>
{/if}
