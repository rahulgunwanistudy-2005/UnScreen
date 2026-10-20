<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { fromEvent, match } from '#lib/a11y/keymap.ts';
	import { prefs } from '#lib/a11y/settings.svelte.ts';
	import { ReaderSession } from '#lib/reader.svelte.ts';
	import AskPanel from '#lib/reader/AskPanel.svelte';
	import ChangesPanel from '#lib/reader/ChangesPanel.svelte';
	import DocView from '#lib/reader/DocView.svelte';
	import SettingsPanel from '#lib/reader/SettingsPanel.svelte';

	const session = new ReaderSession();
	let content: HTMLElement;
	let askPanel: AskPanel;
	let changesPanel: ChangesPanel;

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
		<div class="controls">
			<button class="button" type="button" onclick={() => session.toggle()} aria-describedby="status-line">
				{reading ? 'Stop reading' : 'Start reading the shared screen'}
			</button>
			<button class="button quiet" type="button" onclick={() => session.whereIsPointer()} disabled={!reading}>
				What is the pointer on?
			</button>
			<SettingsPanel onchange={() => session.pushSettings()} />
		</div>
		<p id="status-line" class="status" class:alarm={session.alert !== ''}>
			{session.alert || session.status}
			{#if session.busy}<span class="working">Reading a change.</span>{/if}
		</p>

		<h1>{doc?.title ?? (doc ? 'Shared screen' : 'Read a shared screen')}</h1>

		<section class="content" bind:this={content} tabindex="-1" aria-label="Shared content" onfocusin={onFocusIn}>
			{#if doc}
				<DocView {doc} changed={fresh} />
			{:else if session.phase === 'reading'}
				<p>Waiting for the first picture of the shared screen. This usually takes a few seconds.</p>
			{:else}
				<ol class="steps">
					<li>Join your meeting in another tab or window, as usual.</li>
					<li>Press <strong>Start reading the shared screen</strong>, or Alt+Shift+S.</li>
					<li>Chrome asks what to share. Choose the meeting tab or window. You stay on this page.</li>
					<li>
						Read the shared content here like a web page. Changes are announced politely, and your place is kept.
					</li>
				</ol>
				<p>
					No meeting handy? Open the <a href="/fixture/sheet?seed=1" target="_blank" rel="noopener"
						>test spreadsheet that changes every 8 seconds</a
					> and share that tab.
				</p>
			{/if}
		</section>
	</main>

	<aside aria-label="Changes and questions">
		<ChangesPanel bind:this={changesPanel} history={session.doc.history} />
		<section aria-labelledby="pointer-h">
			<h2 id="pointer-h">Pointer</h2>
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
		gap: 3rem;
		padding-top: 2rem;
	}
	@media (min-width: 1100px) {
		.layout {
			grid-template-columns: minmax(0, 1fr) 22rem;
		}
	}
	main:focus {
		outline: none;
	}
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		align-items: center;
	}
	.status {
		margin: 1rem 0 2rem;
		padding-left: 0.8rem;
		border-left: 4px solid var(--ink);
		color: var(--ink-soft);
	}
	.status.alarm {
		border-color: var(--alarm);
		color: var(--alarm);
		font-weight: 700;
	}
	.working {
		margin-left: 0.5em;
		font-style: italic;
	}
	.content:focus-visible {
		outline-offset: 6px;
	}
	.steps {
		padding-left: 1.4em;
		max-width: var(--measure);
	}
	.steps li {
		margin-bottom: 0.5em;
	}
	aside {
		display: grid;
		gap: 2.5rem;
		align-content: start;
	}
	aside :global(h2) {
		font-size: var(--s1);
		border-bottom: 2px solid var(--ink);
		padding-bottom: 0.3em;
	}
</style>
