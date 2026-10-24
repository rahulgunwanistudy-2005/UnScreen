<script lang="ts">
	import { resolve } from '$app/paths';
	import Icon from '#lib/site/Icon.svelte';
	import { withQuery } from '#lib/site/href.ts';
	import { onDestroy, onMount } from 'svelte';
	import { fromEvent, match } from '#lib/a11y/keymap.ts';
	import { prefs } from '#lib/a11y/settings.svelte.ts';
	import { ReaderSession } from '#lib/reader.svelte.ts';
	import AskPanel from '#lib/reader/AskPanel.svelte';
	import ChangesPanel from '#lib/reader/ChangesPanel.svelte';
	import DocView from '#lib/reader/DocView.svelte';
	import SettingsPanel from '#lib/reader/SettingsPanel.svelte';
	import recording from '#lib/recording/catalog.json';
	import { readRecording } from '#lib/recording/types.ts';

	const session = new ReaderSession();
	let content: HTMLElement;
	let askPanel: AskPanel;
	let changesPanel: ChangesPanel;
	let usingScreenReader = $state(true);
	let hearIt = $state(false);
	let speechAvailable = $state(false);
	let recordingError = $state('');
	let loadingRecording = $state(false);
	async function watchRecording() {
		loadingRecording = true;
		recordingError = '';
		try {
			const response = await fetch('/recordings/session.json');
			if (!response.ok) throw new Error('The recorded session is unavailable.');
			session.playRecording(readRecording(await response.json()));
		} catch {
			recordingError = 'The recorded session could not be loaded. You can still start a live share.';
		} finally { loadingRecording = false; }
	}

	$effect(() => {
		if (usingScreenReader) hearIt = false;
		session.setHearIt(hearIt && !usingScreenReader);
	});

	const reading = $derived(session.phase === 'reading' || session.phase === 'starting');
	const doc = $derived(session.doc.doc);
	const fresh = $derived(
		Object.fromEntries(Object.entries(session.changed).filter(([, v]) => doc && v >= doc.version))
	);

	function onFocusIn(e: FocusEvent) {
		const el = (e.target as HTMLElement | null)?.closest<HTMLElement>('[data-ref]');
		session.setFocus(el?.dataset.ref ?? null);
	}

	function focusRef(ref: string) {
		const el = content?.querySelector<HTMLElement>(`[data-ref="${CSS.escape(ref)}"]`);
		el?.focus();
		return !!el;
	}

	function onKey(e: KeyboardEvent) {
		if (!prefs.value.shortcuts) return;
		const action = match(prefs.value.keymap, fromEvent(e));
		if (!action) return;
		e.preventDefault();
		switch (action) {
			case 'toggleCapture':
				return session.toggle();
			case 'readSummary':
				return session.readSummary();
			case 'whereIsPointer':
				return session.whereIsPointer();
			case 'focusAsk':
				return askPanel.focus();
			case 'focusContent':
				return content.focus();
			case 'focusChanges':
				return changesPanel.focus();
			case 'repeatLast':
				return session.repeatLast();
			case 'cycleVerbosity':
				return session.cycleVerbosity();
			case 'openHelp':
				window.open('/help', '_blank', 'noopener');
		}
	}

	onMount(() => {
		speechAvailable = 'speechSynthesis' in window;
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
	onDestroy(() => session.stop('Stopped reading.'));
</script>

<svelte:head>
	<title>{doc?.title ? `${doc.title} | ` : ''}UnScreen reader</title>
	<meta name="description" content="Read a shared screen from any meeting app with your screen reader." />
</svelte:head>

<div class="live" role="status" aria-live="polite" aria-atomic="true">{session.live}</div>
<div class="visually-hidden" role="alert">{session.alert}</div>

<div class="layout wrap">
	<main id="main" tabindex="-1">
  <div class="reader-heading"><p class="page-note"><Icon name="screen" size={17} /> Your reading space</p><h1>{doc?.title ?? (doc ? 'Shared screen' : 'Read a shared screen')}</h1><p class="reader-description">The shared screen, with room to read at your own pace.</p></div>
		<div class="controls">
			<button class="button" type="button" onclick={() => session.toggle()} aria-describedby="status-line"><Icon name="screen" size={18} />
				{session.phase === 'recording' ? 'Stop recording' : reading ? 'Stop reading' : 'Start reading the shared screen'}
			</button>
			{#if recording.available}
				<button class="button quiet" type="button" onclick={watchRecording} disabled={reading || session.phase === 'recording' || loadingRecording}><Icon name="play" size={16} />Watch a recorded session</button>
			{/if}
			<button class="button quiet" type="button" onclick={() => session.whereIsPointer()} disabled={!reading}>
				<Icon name="pointer" size={16} /> What is the pointer on?
			</button>
			<SettingsPanel onchange={() => session.pushSettings()} />
		</div>
		{#if recordingError}<p role="alert">{recordingError}</p>{/if}
		{#if session.recordingSource}
			<p class="recording-notice"><strong>Recorded session, played at 2× speed.</strong> These are actual engine messages from a real-model run on a generated test sheet. This is a recording, not a live meeting. Source: <code>{session.recordingSource}</code>. Live Ask and pointer requests are disabled during playback.</p>
		{/if}
		<details class="audio-preview">
			<summary>Hear announcements without a screen reader</summary>
			<p id="hear-hint">For sighted demos. Leave this off when NVDA, VoiceOver or another screen reader is speaking, to avoid overlapping voices.</p>
			<label><input type="checkbox" bind:checked={usingScreenReader} /> I am using a screen reader</label>
			<label><input type="checkbox" bind:checked={hearIt} disabled={usingScreenReader || !speechAvailable} aria-describedby="hear-hint" /> Hear it: speak announcements aloud</label>
			{#if !speechAvailable}<p>Speech preview is unavailable in this browser.</p>{/if}
		</details>
		<p id="status-line" class="status" class:alarm={session.alert !== ''}>
			{session.alert || session.status}
			{#if session.busy}<span class="working">Reading a change.</span>{/if}
		</p>

		{#if doc && ['code', 'slide', 'doc'].includes(doc.content_type)}
			<p>Code and slide reading is experimental. The compressed-fixture benchmark found more transcription errors in these views. Check important details with the presenter. <a href={resolve('/(site)/benchmark')}>Read the measured limitations</a>.</p>
		{/if}

		<section class="content" bind:this={content} tabindex="-1" aria-label="Shared content" onfocusin={onFocusIn}>
   <div class="content-bar"><span><Icon name="text" size={17} /> Shared content</span><span class="content-state">{doc ? 'Reconstructed view' : 'Ready when you are'}</span></div>
   <div class="content-body">
			{#if doc}
				<DocView {doc} changed={fresh} />
			{:else if session.phase === 'reading'}
				<p>Waiting for the first picture of the shared screen. This usually takes a few seconds.</p>
			{:else}
				<div class="empty-heading"><span class="empty-icon"><Icon name="screen" size={34} /></span><h2>Bring the meeting into focus.</h2><p>Choose a shared screen. We’ll make a readable space for it here.</p></div>
    <ol class="steps">
					<li>Join your meeting in another tab or window, as usual.</li>
					<li>Press <strong>Start reading the shared screen</strong>, or Alt+Shift+S.</li>
					<li>Chrome asks what to share. Choose the meeting tab or window. You stay on this page.</li>
					<li>
						Read the shared content here like a web page. Changes are announced politely, and your place is kept.
					</li>
				</ol>
				<p>
					No meeting handy? Open the <a href={withQuery(resolve('/fixture/sheet'), 'seed=1')} target="_blank" rel="noopener"
						>test spreadsheet that changes every 8 seconds</a
					> and share that tab.
				</p>
			{/if}
   </div>
		</section>
	</main>

	<aside aria-label="Changes and questions">
		<ChangesPanel bind:this={changesPanel} history={session.doc.history} />
		<section class="pointer-panel" aria-labelledby="pointer-h">
			<h2 id="pointer-h"><Icon name="pointer" size={19} /> Pointer</h2>
			<p>{session.pointerText ?? 'No pointer movement seen yet.'}</p>
			{#if session.pointerRef}
				<button class="button quiet" type="button" onclick={() => focusRef(session.pointerRef!)}>
					Go to what the pointer is on
				</button>
			{/if}
		</section>
		<AskPanel bind:this={askPanel} answers={session.answers} ask={(q) => session.ask(q)} goto={focusRef} enabled={reading} />
	</aside>
</div>

<style>
	.live {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip-path: inset(50%);
	}
	.layout {
		display: grid;
		gap: 1.4rem;
		padding-top: 1.8rem;
	}
	main {
		min-width: 0;
	}
	main:focus {
		outline: none;
	}
	.reader-heading {
		margin-bottom: 1.4rem;
	}
	.page-note {
		display: flex;
		align-items: center;
		gap: .5rem;
		color: var(--accent);
		font-size: .8rem;
		margin-bottom: 1rem;
	}
	.reader-heading h1 {
		font-size: clamp(2rem, 3.5vw, 3rem);
		font-weight: 400;
		margin-bottom: .5rem;
	}
	.reader-description {
		color: var(--ink-soft);
		font-size: .9rem;
	}
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: .65rem;
		align-items: center;
		padding: 1.1rem;
		border: 1px solid var(--rule);
		background: var(--surface);
		border-radius: 16px;
	}
	.controls :global(.button) {
		font-size: .8rem;
		min-height: 2.5rem;
		padding-inline: 1rem;
	}
	.status {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: .5rem;
		margin: 1.3rem 0;
		padding: .75rem 1rem;
		border: 1px solid var(--rule);
		border-radius: 10px;
		color: var(--ink-soft);
		background: var(--surface);
		font-size: .85rem;
	}
	.status::before {
		content: '';
		width: .4rem;
		height: .4rem;
		flex: 0 0 auto;
		border-radius: 50%;
		background: var(--accent);
		margin-right: .25rem;
	}
	.status.alarm {
		border-color: var(--alarm);
		color: var(--alarm);
		font-weight: 600;
	}
	.status.alarm::before {
		background: var(--alarm);
	}
	.audio-preview {
		margin-top: 1rem;
		max-width: var(--measure);
		color: var(--ink-soft);
		font-size: .8rem;
		padding: .2rem .2rem;
	}
	.audio-preview summary {
		color: var(--ink-soft);
	}
	.audio-preview p {
		margin-top: .7rem;
	}
	.audio-preview label {
		display: flex;
		align-items: start;
		gap: .5em;
		margin-block: .6rem;
	}
	.recording-notice {
		border: 1px solid var(--rule);
		border-radius: 12px;
		padding: 1rem;
		background: var(--surface-raised);
		font-size: .85rem;
		margin-top: 1rem;
		overflow-wrap: anywhere;
	}
	.working {
		font-style: italic;
	}
	.content {
		min-width: 0;
		border: 1px solid var(--rule);
		border-radius: 18px;
		background: var(--surface);
		box-shadow: var(--shadow);
		overflow: hidden;
	}
	.content:focus-visible {
		outline-offset: 6px;
	}
	.content-bar {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
		padding: 1rem 1.3rem;
		border-bottom: 1px solid var(--rule);
		font-size: .8rem;
	}
	.content-bar > span:first-child {
		display: flex;
		align-items: center;
		gap: .5rem;
	}
	.content-state {
		color: var(--ink-soft);
		font-size: .7rem;
	}
	.content-body {
		padding: 1.5rem;
		min-height: 23rem;
	}
	.empty-heading {
		padding: 1rem 0 .5rem;
	}
	.empty-icon {
		display: inline-flex;
		padding: 1rem;
		border: 1px solid var(--rule);
		background: var(--surface-raised);
		border-radius: 18px;
		color: var(--accent);
		margin-bottom: 1.5rem;
		box-shadow: 0 0 45px var(--ambient);
	}
	.empty-heading h2 {
		font-size: 1.7rem;
	}
	.empty-heading p {
		color: var(--ink-soft);
		font-size: .85rem;
	}
	.steps {
		padding-left: 1.3em;
		max-width: var(--measure);
		color: var(--ink-soft);
		font-size: .9rem;
	}
	.steps li {
		margin-bottom: .8em;
		padding-left: .3em;
	}
	.steps li::marker {
		color: var(--accent);
	}
	.content-body > p {
		font-size: .85rem;
		color: var(--ink-soft);
	}
	aside {
		display: grid;
		gap: 1rem;
		align-content: start;
		min-width: 0;
	}
	aside :global(section) {
		padding: 1.4rem;
		background: var(--surface);
		border: 1px solid var(--rule);
		border-radius: 16px;
		min-width: 0;
	}
	aside :global(h2) {
		display: flex;
		align-items: center;
		gap: .6rem;
		font-size: 1rem;
		margin-bottom: 1rem;
	}
	aside :global(h2 svg) {
		color: var(--accent);
		flex-shrink: 0;
	}
	aside :global(p), aside :global(label) {
		font-size: .85rem;
	}
	aside :global(p) {
		color: var(--ink-soft);
		margin-bottom: 0;
	}
	aside :global(.button) {
		font-size: .8rem;
	}
	.pointer-panel p {
		border-left: 2px solid var(--mosaic);
		padding-left: .85rem;
	}
	.pointer-panel .button {
		margin-top: 1rem;
	}
	@media (min-width: 1100px) {
		.layout {
			grid-template-columns: minmax(0, 1fr) 21rem;
		}
		aside {
			padding-top: .3rem;
		}
	}
	@media (max-width: 650px) {
		.layout {
			padding-top: 1.5rem;
		}
		.controls {
			padding: .8rem;
		}
		.controls > .button {
			width: 100%;
		}
		.content-body {
			padding: 1rem;
		}
		.content-bar {
			padding: .9rem 1rem;
		}
		.content-state {
			display: none;
		}
	}
</style>
