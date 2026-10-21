<script lang="ts">
	import { ACTION_LABELS, conflict, DEFAULT_KEYMAP, describe, fromEvent, type Action } from '#lib/a11y/keymap.ts';
	import { prefs } from '#lib/a11y/settings.svelte.ts';

	const actions = Object.keys(ACTION_LABELS) as Action[];
	let recording = $state<Action | null>(null);
	let message = $state('');

	function record(action: Action) {
		recording = action;
		message = `Press the new shortcut for "${ACTION_LABELS[action]}". Press Escape to cancel.`;
	}

	function onKey(e: KeyboardEvent, action: Action) {
		if (recording !== action) return;
		if (['Shift', 'Alt', 'Control', 'Meta'].includes(e.key)) return;
		e.preventDefault();
		e.stopPropagation();
		if (e.key === 'Escape') {
			recording = null;
			message = 'Cancelled. The shortcut is unchanged.';
			return;
		}
		const chord = fromEvent(e);
		const problem = conflict(prefs.value.keymap, action, chord);
		if (problem) {
			message =
				problem.reason === 'bare'
					? 'Shortcuts need Alt, Ctrl or Cmd, so they do not clash with screen reader quick keys. Try again.'
					: problem.reason === 'reserved'
						? `${describe(chord)} is used by screen readers or the browser. Try another.`
						: `${describe(chord)} is already used for "${ACTION_LABELS[problem.with!]}". Try another.`;
			return;
		}
		prefs.update({ keymap: { ...prefs.value.keymap, [action]: chord } });
		recording = null;
		message = `"${ACTION_LABELS[action]}" is now ${describe(chord)}.`;
	}

	function turnOff(action: Action) {
		prefs.update({ keymap: { ...prefs.value.keymap, [action]: null } });
		message = `"${ACTION_LABELS[action]}" has no shortcut now.`;
	}

	function reset() {
		prefs.update({ keymap: DEFAULT_KEYMAP });
		message = 'All shortcuts are back to their defaults.';
	}
</script>

<svelte:head>
	<title>Help and keyboard shortcuts | UnScreen</title>
	<meta name="description" content="Keyboard shortcuts and screen reader tips for NVDA, VoiceOver and ChromeVox." />
</svelte:head>

<main id="main" class="wrap help">
	<h1>Help and keyboard shortcuts</h1>
	<p>
		Shortcuts work on the reader page. They all use Alt+Shift (Option+Shift on a Mac), which NVDA, JAWS, VoiceOver and
		ChromeVox leave free, so your screen reader's own keys keep working.
	</p>

	<h2 id="keys">Shortcuts</h2>
	<p class="live" role="status">{message}</p>
	<label class="toggle">
		<input type="checkbox" checked={prefs.value.shortcuts} onchange={(e) => prefs.update({ shortcuts: e.currentTarget.checked })} />
		Use keyboard shortcuts
	</label>
	<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
	<div class="scroll" role="region" aria-label="Keyboard shortcuts, scrollable" tabindex="0">
	<table class="keys">
		<caption class="visually-hidden">Keyboard shortcuts, {actions.length} actions</caption>
		<thead>
			<tr><th scope="col">Action</th><th scope="col">Shortcut</th><th scope="col">Change</th></tr>
		</thead>
		<tbody>
			{#each actions as action (action)}
				<tr>
					<th scope="row">{ACTION_LABELS[action]}</th>
					<td><kbd>{describe(prefs.value.keymap[action])}</kbd></td>
					<td class="change">
						<button
							type="button"
							class="button quiet"
							aria-label="Change shortcut for {ACTION_LABELS[action]}"
							onclick={() => record(action)}
							onkeydown={(e) => onKey(e, action)}
							aria-pressed={recording === action}>{recording === action ? 'Press keys now' : 'Change'}</button
						>
						<button type="button" class="button quiet" aria-label="Turn off shortcut for {ACTION_LABELS[action]}" onclick={() => turnOff(action)}>Turn off</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	</div>
	<p><button type="button" class="button quiet" onclick={reset}>Reset all shortcuts</button></p>

	<h2>Reading the shared screen</h2>
	<ul>
		<li>A spreadsheet becomes a real table with column headers. When the first column names each row, it is used as the row header too.</li>
		<li>Code becomes a listing with one line per line of code, each starting with its line number.</li>
		<li>Slides and documents become headings, paragraphs and lists.</li>
		<li>
			Anything UnScreen could not read clearly says <em>unreadable</em> or <em>unclear</em>. Unclear changes are announced
			as "possibly changed, unclear" and never as a value. Check them with the presenter.
		</li>
		<li>Changes appear in the Changes list, newest first. Choose one to read that earlier version.</li>
	</ul>

	<h2>NVDA on Windows</h2>
	<ul>
		<li>Stay in browse mode. Press T to jump to the table, then Ctrl+Alt+arrow keys to move by cell. NVDA reads the row and column headers as you move.</li>
		<li>Announcements are polite: NVDA finishes what it is saying first. Your reading position does not move when the table updates.</li>
		<li>If the page seems stale, NVDA+F5 refreshes NVDA's view of it.</li>
		<li>For code, use the arrow keys line by line. Each line starts with its number.</li>
	</ul>

	<h2>VoiceOver on macOS</h2>
	<ul>
		<li>Use Chrome or Safari. Press VO+Command+T to jump to the table, then VO+arrow keys to move by cell.</li>
		<li>Option+Shift shortcuts work while VoiceOver is on, because VoiceOver uses Control+Option.</li>
	</ul>

	<h2>ChromeVox on ChromeOS</h2>
	<ul>
		<li>Press Search+Control+arrow keys to move through table cells. Search+T jumps to the next table.</li>
	</ul>

	<h2>If something goes wrong</h2>
	<ul>
		<li><strong>Chrome did not ask what to share:</strong> press Start again. If you cancelled, nothing was shared.</li>
		<li><strong>"Sharing ended":</strong> the meeting tab was closed or sharing was stopped from Chrome's bar. Press Start to choose it again.</li>
		<li><strong>"Engine busy":</strong> the reading service is overloaded. The last version stays on screen; UnScreen will not announce guesses.</li>
	</ul>
</main>

<style>
	.help {
		padding-top: 2rem;
	}
	.help h2 {
		margin-top: 2.5rem;
	}
	.help ul {
		max-width: var(--measure);
		padding-left: 1.2em;
	}
	.help li {
		margin-bottom: 0.5em;
	}
	.toggle {
		display: flex;
		gap: 0.6em;
		align-items: center;
		margin-bottom: 1rem;
	}
	.toggle input {
		width: 1.2rem;
		height: 1.2rem;
		accent-color: var(--ink);
	}
	.scroll {
		overflow-x: auto;
		max-width: 100%;
	}
	.keys {
		border-collapse: collapse;
		width: 100%;
		max-width: 52rem;
	}
	.keys th,
	.keys td {
		text-align: start;
		padding: 0.5em 0.8em 0.5em 0;
		border-bottom: 1px solid var(--rule);
		vertical-align: middle;
	}
	.keys thead th {
		border-bottom: 2px solid var(--ink);
	}
	.keys tbody th {
		font-weight: 400;
	}
	kbd {
		font-family: var(--font-mono);
		font-weight: 700;
		white-space: nowrap;
	}
	.change {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}
	@media (max-width: 480px) {
		.change :global(.button) {
			padding-inline: 0.6em;
		}
	}
	.live {
		min-height: 1.55em;
		font-weight: 700;
	}
</style>
