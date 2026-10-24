<script lang="ts">
	import Icon from '#lib/site/Icon.svelte';
	import { resolve } from '$app/paths';
	import { prefs, type Preferences } from '#lib/a11y/settings.svelte.ts';

	let { onchange }: { onchange: () => void } = $props();

	let dialog: HTMLDialogElement;

	function set<K extends keyof Preferences>(key: K, value: Preferences[K]) {
		prefs.update({ [key]: value } as Partial<Preferences>);
		onchange();
	}
</script>

<button class="button quiet" type="button" onclick={() => dialog.showModal()}><Icon name="settings" size={17} /> Settings</button>

<dialog bind:this={dialog} aria-labelledby="settings-h">
	<h2 id="settings-h">Settings</h2>
	<form method="dialog">
		<fieldset>
			<legend>What to announce</legend>
			{#each [['all', 'Every change'], ['important', 'Important changes: new content, rows or lines added or removed, scrolling'], ['quiet', 'Only changes in the row, column or line you are on']] as [value, label] (value)}
				<label class="choice">
					<input
						type="radio"
						name="verbosity"
						{value}
						checked={prefs.value.verbosity === value}
						onchange={() => set('verbosity', value as Preferences['verbosity'])}
					/>
					{label}
				</label>
			{/each}
		</fieldset>
		<fieldset>
			<legend>Changed numbers</legend>
			<label class="choice">
				<input type="radio" name="numeric" checked={prefs.value.numericStyle === 'old_to_new'} onchange={() => set('numericStyle', 'old_to_new')} />
				Say the old and the new value
			</label>
			<label class="choice">
				<input type="radio" name="numeric" checked={prefs.value.numericStyle === 'new_only'} onchange={() => set('numericStyle', 'new_only')} />
				Say only the new value
			</label>
		</fieldset>
		<fieldset>
			<legend>Display</legend>
			<label class="choice">
				<input type="checkbox" checked={prefs.value.largePrint} onchange={(e) => set('largePrint', e.currentTarget.checked)} />
				Large print
			</label>
			<label class="choice">
				<input type="checkbox" checked={prefs.value.motion === 'reduce'} onchange={(e) => set('motion', e.currentTarget.checked ? 'reduce' : 'system')} />
				Reduce motion
			</label>
			<label class="field">
				Theme
				<select value={prefs.value.theme} onchange={(e) => set('theme', e.currentTarget.value as Preferences['theme'])}>
					<option value="system">Match my system</option>
					<option value="light">Light</option>
					<option value="dark">Dark, high contrast</option>
				</select>
			</label>
		</fieldset>
		<p class="note">Keyboard shortcuts can be changed or turned off on the <a href={resolve('/(site)/help')}>help page</a>.</p>
		<button class="button" type="submit">Done</button>
	</form>
</dialog>

<style>
	dialog {
		max-width: min(36rem, calc(100vw - 2rem));
		border: 1px solid var(--rule);
		border-radius: 20px;
		background: var(--surface);
		color: var(--ink);
		padding: 2rem;
		box-shadow: var(--shadow);
	}
	dialog::backdrop {
		background: rgb(0 5 15 / 0.8);
		backdrop-filter: blur(8px);
	}
	fieldset {
		border: 0;
		border-top: 1px solid var(--rule);
		padding: 0.75rem 0 1rem;
		margin: 0;
	}
	legend {
		font-weight: 800;
		padding: 0;
	}
	.choice {
		display: flex;
		gap: 0.6em;
		align-items: baseline;
		padding-block: 0.3em;
	}
	.choice input {
		width: 1.2rem;
		height: 1.2rem;
		accent-color: var(--ink);
	}
	.field {
		display: grid;
		gap: 0.3em;
		margin-top: 0.5em;
		font-weight: 700;
	}
	.note {
		font-size: var(--s-1);
	}
</style>
