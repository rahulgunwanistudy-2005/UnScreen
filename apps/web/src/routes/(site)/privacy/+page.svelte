<script lang="ts">
	import Icon from '#lib/site/Icon.svelte';
</script>

<svelte:head>
	<title>Privacy | UnScreen</title>
	<meta name="description" content="What UnScreen does with your shared screen." />
</svelte:head>

<main id="main" class="wrap prose">
	<p class="page-note"><Icon name="shield" size={18} /> A clear view of your data</p>
	<h1>Privacy</h1>
	<p>UnScreen reads the tab or window you choose to share. Here is exactly what happens to it.</p>
	<p>This project is currently being validated locally. The owner has confirmed paid Gemini billing and an active Mistral plan. There is no hosted instance from this completion session. The default configuration uses Gemini for reading and cross-checking; optional provider configurations must be disclosed before hosting.</p>

	<section aria-labelledby="leaves"><h2 id="leaves">What leaves your computer</h2>
	<ul>
		<li>
			When the shared screen changes, UnScreen sends a picture of it to the UnScreen engine. The engine sends that
			picture, or a cropped part of it, to <strong>Google's Gemini API</strong> to read the text and structure.
		</li>
		<li>Questions you type in Ask are sent to the Gemini API together with the current picture.</li>
		<li>Nothing is sent while the screen is not changing, and nothing is sent after you press Stop.</li>
	</ul>

	</section><section aria-labelledby="keeps"><h2 id="keeps">What UnScreen keeps</h2>
	<ul>
		<li>Pictures are held in the engine's memory only while they are being read, plus the latest few for comparison. The live engine never writes them to disk or a database. The generated benchmark fixtures in the repository are separate test content.</li>
		<li>The reconstructed text of the current session is kept in memory and deleted 30 minutes after you disconnect.</li>
		<li>There are no accounts, no analytics on what you share, and no cookies.</li>
		<li>Your settings and keyboard shortcuts are saved in this browser only.</li>
		<li>The daily spending ledger stores dates, model-call counts and estimated dollar totals. It contains no pictures, reconstructed text, questions or API keys.</li>
	</ul>

	</section><section aria-labelledby="google"><h2 id="google">What Google does</h2>
	<p>Requests to the Gemini API are covered by Google's own terms, which differ by tier:</p>
	<ul>
		<li>
			<strong>Free tier:</strong> Google may use what is sent, and the replies, to improve its products, and human reviewers
			may read them.
		</li>
		<li>
			<strong>Paid tier:</strong> Google does not use them to improve its products, but logs them for a limited time to
			detect misuse.
		</li>
	</ul>
	<p>
		Read <a href="https://ai.google.dev/gemini-api/terms">the Gemini API terms</a> before sharing anything confidential.
	</p>
	<p>UnScreen sets <code>store=false</code> on Gemini Interactions requests, so those interactions are not stored for later retrieval. This does not remove Google's separate abuse-monitoring obligations. Optional Groq and Mistral configurations send content to those providers instead; their terms and the configured tier must be reviewed before use.</p>

	</section><section aria-labelledby="before"><h2 id="before">Before you share</h2>
	<p>
		Only share content you are allowed to share with a third-party service. If a meeting is confidential, ask the
		presenter first, or do not use UnScreen for it.
	</p>
</section>
</main>

<style>
	.page-note {
		display: flex;
		align-items: center;
		gap: .55rem;
		color: var(--accent);
		font-size: .8rem;
	}
	.prose > h1 {
		font-size: clamp(2.2rem, 4vw, 3.5rem);
		font-weight: 400;
	}
	.prose > p:not(.page-note) {
		color: var(--ink-soft);
	}
	.prose section {
		max-width: 54rem;
		padding: 2rem;
		margin-top: 1.2rem;
		border: 1px solid var(--rule);
		border-radius: 18px;
		background: var(--surface);
	}
	.prose section h2 {
		margin-top: 0;
		font-size: 1.6rem;
	}
	.prose section p,.prose section ul {
		color: var(--ink-soft);
	}
	.prose section strong {
		color: var(--ink);
		font-weight: 600;
	}
	.prose section :last-child {
		margin-bottom: 0;
	}
	@media (max-width: 600px) {
		.prose section {
			padding: 1.3rem;
		}
	}
	.prose {
		padding-top: 3rem;
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
