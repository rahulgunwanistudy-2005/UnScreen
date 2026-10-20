<script lang="ts">
	import type { Code } from '@unscreen/schema';

	let {
		code,
		title,
		changed = {},
		idPrefix = ''
	}: { code: Code; title: string | null; changed?: Record<string, number>; idPrefix?: string } = $props();

	const name = $derived(code.file_name ?? title ?? 'Shared code');
</script>

<figure aria-labelledby="{idPrefix}code-caption">
	<figcaption id="{idPrefix}code-caption">
		{name}{code.language ? `, ${code.language}` : ''}, {code.lines.length}
		{code.lines.length === 1 ? 'line' : 'lines'}
	</figcaption>
	<pre><code
			>{#each code.lines as line, i (line.id)}<span
					class="line"
					class:fresh={changed[line.id] !== undefined}
					class:uncertain={line.uncertain || line.unreadable}
					id="{idPrefix}{line.id}"
					data-ref={line.id}
					tabindex="-1"><span class="n">{line.n ?? i + 1}</span><span class="t"
						>{#if line.unreadable}<em>unreadable</em>{:else}{line.text || ' '}{#if line.uncertain}<em> (unclear)</em
							>{/if}{/if}</span
					></span
				>{/each}</code
		></pre>
</figure>

<style>
	figure {
		margin: 0;
	}
	figcaption {
		font-weight: 700;
		color: var(--ink-soft);
		margin-bottom: 0.6em;
	}
	pre {
		margin: 0;
		overflow-x: auto;
		font-family: var(--font-mono);
		font-size: var(--s0);
		line-height: 1.6;
		border-top: 2px solid var(--ink);
		border-bottom: 2px solid var(--ink);
		padding-block: 0.5em;
	}
	.line {
		display: flex;
		white-space: pre;
	}
	.n {
		flex: none;
		width: 4ch;
		padding-right: 1.5ch;
		text-align: right;
		color: var(--ink-soft);
	}
	.n::after {
		content: '';
	}
	.fresh {
		background: var(--signal);
		color: var(--on-signal);
	}
	.fresh .n {
		color: var(--on-signal);
	}
	.uncertain .t {
		text-decoration: underline wavy;
		text-decoration-thickness: 1px;
	}
	.line:focus-visible {
		outline-offset: -3px;
	}
</style>
