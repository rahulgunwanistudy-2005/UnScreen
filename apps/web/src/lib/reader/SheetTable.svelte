<script lang="ts">
	import type { Cell, Sheet } from '@unscreen/schema';

	let {
		sheet,
		title,
		changed = {},
		idPrefix = ''
	}: { sheet: Sheet; title: string | null; changed?: Record<string, number>; idPrefix?: string } = $props();

	const keyed = $derived(sheet.rows.length > 0 && sheet.rows.filter((r) => r.key).length >= sheet.rows.length * 0.8);
</script>

{#snippet value(cell: Cell)}
	{#if cell.unreadable}<span class="flag">unreadable</span>{:else}{cell.text}{#if cell.uncertain}<span class="flag"
				>&nbsp;(unclear)</span
			>{/if}{/if}
{/snippet}

<div class="scroller" role="region" aria-label="{title ?? 'Shared spreadsheet'}, scrollable" tabindex="-1">
	<table>
		<caption>
			{title ?? sheet.sheet_name ?? 'Shared spreadsheet'}, {sheet.rows.length}
			{sheet.rows.length === 1 ? 'row' : 'rows'}, {sheet.columns.length}
			{sheet.columns.length === 1 ? 'column' : 'columns'}
		</caption>
		<thead>
			<tr>
				{#each sheet.columns as col (col.id)}
					<th
						scope="col"
						id="{idPrefix}{col.id}"
						data-ref={col.id}
						tabindex="-1"
						class:uncertain={col.uncertain || col.unreadable}
						class:fresh={changed[col.id] !== undefined}>{@render value(col)}</th
					>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each sheet.rows as row (row.id)}
				<tr data-ref={row.id}>
					{#each row.cells as cell, j (cell.id)}
						{#if j === 0 && keyed}
							<th
								scope="row"
								id="{idPrefix}{cell.id}"
								data-ref={cell.id}
								tabindex="-1"
								class:uncertain={cell.uncertain || cell.unreadable}
								class:fresh={changed[cell.id] !== undefined}>{@render value(cell)}</th
							>
						{:else}
							<td
								id="{idPrefix}{cell.id}"
								data-ref={cell.id}
								tabindex="-1"
								class:uncertain={cell.uncertain || cell.unreadable}
								class:fresh={changed[cell.id] !== undefined}>{@render value(cell)}</td
							>
						{/if}
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.scroller {
		overflow-x: auto;
		max-width: 100%;
	}
	table {
		border-collapse: collapse;
		font-size: var(--s0);
		min-width: min(100%, 36rem);
	}
	caption {
		text-align: start;
		font-weight: 700;
		padding-block: 0 0.6em;
		color: var(--ink-soft);
	}
	th,
	td {
		padding: 0.45em 0.9em;
		border-bottom: 1px solid var(--rule);
		text-align: start;
		vertical-align: top;
		white-space: nowrap;
	}
	thead th {
		border-bottom: 2px solid var(--ink);
		font-weight: 800;
	}
	tbody th {
		font-weight: 700;
	}
	td:focus-visible,
	th:focus-visible {
		outline-offset: -3px;
	}
	.fresh {
		background: var(--signal);
		color: var(--on-signal);
	}
	.uncertain {
		text-decoration: underline wavy;
		text-decoration-thickness: 1px;
		text-underline-offset: 0.25em;
	}
	.flag {
		font-style: italic;
	}
</style>
