<script lang="ts">
	import type { AnswerEntry } from '#lib/reader.svelte.ts';

	let {
		answers,
		ask,
		goto,
		enabled
	}: { answers: AnswerEntry[]; ask: (q: string) => boolean; goto: (ref: string) => boolean; enabled: boolean } = $props();

	let q = $state('');
	let input: HTMLInputElement;

	export function focus() {
		input.focus();
	}

	function submit(e: SubmitEvent) {
		e.preventDefault();
		if (ask(q)) q = '';
	}
</script>

<section aria-labelledby="ask-h">
	<h2 id="ask-h">Ask about the screen</h2>
	<form onsubmit={submit}>
		<label for="ask-q">Question</label>
		<div class="row">
			<input id="ask-q" type="text" bind:this={input} bind:value={q} maxlength="500" autocomplete="off" aria-describedby="ask-hint" />
			<button class="button" type="submit" disabled={!enabled}>Ask</button>
		</div>
		<p id="ask-hint" class="hint">For example: which account has the highest Q3 revenue? Answers name the cells they use.</p>
	</form>
	{#if answers.length > 0}
		<ol class="answers" reversed>
			{#each answers as a, i (i)}
				<li>
					<p class="q">{a.q}</p>
					<p>{a.text}</p>
					{#if a.refs.length > 0}
						<p class="refs">
							Based on:
							{#each a.refs as ref, k (ref)}
								<button type="button" class="ref" onclick={() => goto(ref)}>{ref}</button>{k < a.refs.length - 1 ? ' ' : ''}
							{/each}
						</p>
					{/if}
				</li>
			{/each}
		</ol>
	{/if}
</section>

<style>
	label {
		display: block;
		font-weight: 700;
		margin-bottom: 0.3em;
	}
	.row {
		display: flex;
		gap: 0.5rem;
	}
	.row input {
		flex: 1;
		min-width: 0;
	}
	.hint {
		font-size: var(--s-1);
		color: var(--ink-soft);
		margin-top: 0.5em;
	}
	.answers {
		list-style: none;
		padding: 0;
		margin: 1.5rem 0 0;
	}
	.answers li {
		border-top: 1px solid var(--rule);
		padding-top: 0.75rem;
		margin-bottom: 1rem;
	}
	.q {
		font-weight: 700;
		margin-bottom: 0.3em;
	}
	.refs {
		font-size: var(--s-1);
	}
	.ref {
		background: none;
		border: 1px solid var(--ink);
		border-radius: 2px;
		padding: 0.1em 0.4em;
		cursor: pointer;
		font-family: var(--font-mono);
	}
</style>
