<svelte:head>
	<title>Privacy | UnScreen</title>
	<meta name="description" content="What UnScreen does with your shared screen." />
</svelte:head>

<main id="main" class="wrap prose">
	<h1>Privacy</h1>
	<p>UnScreen reads the tab or window you choose to share. Here is exactly what happens to it.</p>

	<h2>What leaves your computer</h2>
	<ul>
		<li>
			When the shared screen changes, UnScreen sends a picture of it to the UnScreen engine. The engine sends that
			picture, or a cropped part of it, to <strong>Google's Gemini API</strong> to read the text and structure.
		</li>
		<li>Questions you type in Ask are sent to the Gemini API together with the current picture.</li>
		<li>Nothing is sent while the screen is not changing, and nothing is sent after you press Stop.</li>
	</ul>

	<h2>What UnScreen keeps</h2>
	<ul>
		<li>Pictures are held in the engine's memory only while they are being read, plus the latest few for comparison. They are never written to disk or a database.</li>
		<li>The reconstructed text of the current session is kept in memory and deleted 30 minutes after you disconnect.</li>
		<li>There are no accounts, no analytics on what you share, and no cookies.</li>
		<li>Your settings and keyboard shortcuts are saved in this browser only.</li>
	</ul>

	<h2>What Google does</h2>
	<p>
		Requests to the Gemini API are covered by Google's own terms. On Google's paid tier, Google says it does not use prompts
		or responses to improve its products; on the free tier it may. Read
		<a href="https://ai.google.dev/gemini-api/terms">the Gemini API terms</a> before sharing anything confidential.
	</p>

	<h2>Before you share</h2>
	<p>
		Only share content you are allowed to share with a third-party service. If a meeting is confidential, ask the
		presenter first, or do not use UnScreen for it.
	</p>
</main>

<style>
	.prose {
		padding-top: 2rem;
	}
	.prose ul {
		max-width: var(--measure);
		padding-left: 1.2em;
	}
	.prose li {
		margin-bottom: 0.5em;
	}
	.prose h2 {
		margin-top: 2rem;
	}
</style>
