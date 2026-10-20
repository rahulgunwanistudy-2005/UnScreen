<script lang="ts">
	import type { SheetFixture } from './sheet.ts';

	let {
		sheet,
		firstRow = 0,
		maxRows = 99,
		selected = null
	}: {
		sheet: SheetFixture;
		firstRow?: number;
		maxRows?: number;
		selected?: { row: number; col: number } | null;
	} = $props();

	const letters = 'ABCDEFGHIJKLMNOP';
	const visible = $derived(sheet.rows.slice(firstRow, firstRow + maxRows));
	const numeric = (v: string) => /^[$\d][\d,.$K%]*$/.test(v);
	const formula = $derived(selected ? (sheet.rows[selected.row]?.[selected.col] ?? '') : '');
</script>

<div
	class="app"
	class:dark={sheet.style.theme === 'dark'}
	style:--font={sheet.style.font}
	style:--size="{sheet.style.fontPx}px"
	style:--head={sheet.style.headerFill}
>
	<header class="top">
		<div class="doc-icon"></div>
		<div>
			<div class="doc-title">{sheet.title}</div>
			<div class="menu">File Edit View Insert Format Data Tools Help</div>
		</div>
	</header>
	<div class="formula">
		<span class="ref">{selected ? `${letters[selected.col]}${selected.row + 2}` : 'A1'}</span>
		<span class="fx">fx</span>
		<span class="fval">{formula}</span>
	</div>
	<div class="grid-wrap">
		<table class="grid" class:lines={sheet.style.gridlines}>
			<thead>
				<tr class="letters">
					<th class="corner"></th>
					{#each sheet.columns as _, c (c)}
						<th>{letters[c]}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				<tr class="header-row">
					<td class="rownum">1</td>
					{#each sheet.columns as col, c (c)}
						<td class:bold={sheet.style.boldHeader} data-truth="h{c}">{col.header}</td>
					{/each}
				</tr>
				{#each visible as row, i (row[0])}
					<tr class:zebra={sheet.style.zebra && i % 2 === 1}>
						<td class="rownum">{firstRow + i + 2}</td>
						{#each row as value, c (c)}
							<td
								class:num={numeric(value)}
								class:sel={selected?.row === firstRow + i && selected?.col === c}
								data-truth="r{i}c{c}">{value}</td
							>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<footer class="tabs">
		<span class="tab active">{sheet.sheetName}</span>
		<span class="tab">Notes</span>
	</footer>
</div>

<style>
	.app {
		--bg: #ffffff;
		--fg: #202124;
		--chrome: #f8f9fa;
		--line: #e2e3e3;
		--muted: #5f6368;
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		background: var(--bg);
		color: var(--fg);
		font-family: var(--font);
		font-size: var(--size);
	}
	.dark {
		--bg: #1e1f20;
		--fg: #e3e3e3;
		--chrome: #28292a;
		--line: #3c3d3e;
		--muted: #a8abae;
	}
	.top {
		display: flex;
		gap: 12px;
		align-items: center;
		padding: 10px 16px;
		background: var(--chrome);
	}
	.doc-icon {
		width: 28px;
		height: 36px;
		border-radius: 3px;
		background: #188038;
	}
	.doc-title {
		font-size: 18px;
		font-family: Arial, sans-serif;
	}
	.menu {
		font-size: 13px;
		color: var(--muted);
		font-family: Arial, sans-serif;
		word-spacing: 10px;
	}
	.formula {
		display: flex;
		gap: 14px;
		align-items: center;
		padding: 4px 12px;
		border-block: 1px solid var(--line);
		font-size: 13px;
		font-family: Arial, sans-serif;
	}
	.ref {
		width: 60px;
		color: var(--muted);
	}
	.fx {
		color: var(--muted);
		font-style: italic;
	}
	.grid-wrap {
		flex: 1;
		overflow: hidden;
	}
	.grid {
		border-collapse: collapse;
	}
	.grid td,
	.grid th {
		padding: 4px 10px;
		white-space: nowrap;
		min-width: 90px;
		height: 1.9em;
	}
	.lines td {
		border: 1px solid var(--line);
	}
	.letters th {
		background: var(--chrome);
		color: var(--muted);
		font-weight: normal;
		font-size: 12px;
		font-family: Arial, sans-serif;
		border: 1px solid var(--line);
	}
	.corner {
		min-width: 40px !important;
		width: 40px;
	}
	.rownum {
		background: var(--chrome);
		color: var(--muted);
		text-align: center;
		font-size: 12px;
		font-family: Arial, sans-serif;
		min-width: 40px !important;
		width: 40px;
	}
	.header-row td:not(.rownum) {
		background: var(--head);
	}
	.bold {
		font-weight: bold;
	}
	.num {
		text-align: right;
	}
	.zebra td:not(.rownum) {
		background: color-mix(in srgb, var(--fg) 4%, var(--bg));
	}
	.sel {
		outline: 2px solid #1a73e8;
		outline-offset: -2px;
	}
	.tabs {
		display: flex;
		gap: 4px;
		padding: 4px 12px;
		background: var(--chrome);
		font-size: 13px;
		font-family: Arial, sans-serif;
	}
	.tab {
		padding: 4px 14px;
		color: var(--muted);
	}
	.active {
		background: var(--bg);
		color: #188038;
		font-weight: bold;
	}
</style>
