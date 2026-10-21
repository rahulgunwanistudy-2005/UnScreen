<script lang="ts">
	import { resolve } from '$app/paths';
	import { withQuery } from '#lib/site/href.ts';
	import { date, headline, pct } from '#lib/bench/format.ts';
	import Hero from '#lib/hero/Hero.svelte';

	const run = headline?.run;
	const o = run?.overall;
	const VARIANTS: Record<string, string> = {
		'720p': 'plain 720p captures',
		'1080p': 'plain 1080p captures',
		'1080p-degraded': 'shares inside a meeting window, sent at 720p with lossy compression'
	};
	const kinds = [...new Set(Object.keys(run?.groups ?? {}).map((g) => g.split('/')[0]))];
	const variants = [...new Set(Object.keys(run?.groups ?? {}).map((g) => g.split('/')[1]))].map((v) => VARIANTS[v] ?? v);
</script>

<svelte:head>
	<title>UnScreen: every screen share, readable by a screen reader</title>
	<meta
		name="description"
		content="UnScreen rebuilds a shared screen from any meeting app as a real table, code listing or outline that NVDA, VoiceOver and ChromeVox can read, and announces what changed."
	/>
</svelte:head>

<main id="main" class="wrap landing">
	<section class="intro" aria-labelledby="title">
		<h1 id="title">Every screen share, readable by a screen reader, live.</h1>
		<p class="lead">
			Zoom, Google Meet and Microsoft Teams send shared content as a picture, so a screen reader can only say that someone
			is sharing. UnScreen reads the picture and rebuilds it as a real table, code listing or outline you can move through,
			then tells you what changed.
		</p>
		<p class="actions">
			<a class="button" href={resolve('/(site)/app')}>Start reading a shared screen</a>
			<a href={withQuery(resolve('/fixture/sheet'), 'seed=1')} target="_blank" rel="noopener">Open a test spreadsheet to share (new tab)</a>
		</p>
	</section>

	<Hero />

	<section aria-labelledby="problem">
		<h2 id="problem">The barrier</h2>
		<p>
			In a study of 65 desktop and 94 mobile screen reader users, Zoom, Meet and Teams all rendered shared content as an
			image (<a href="https://dl.acm.org/doi/full/10.1145/3573012">Leporini, Buzzi and Hersh, ACM TACCESS 2023</a>). A blind
			participant could tell a whiteboard was being shared, but not what was written or erased on it (<a
				href="https://pmc.ncbi.nlm.nih.gov/articles/PMC9483261/">PMC9483261</a
			>). Screen reader OCR is the fallback, and users describe it as ranging from very successful to useless (<a
				href="https://webaim.org/blog/tips-for-accessible-screen-sharing/">WebAIM</a
			>). It reads flat lines, so a spreadsheet loses its rows and columns.
		</p>
	</section>

	<section aria-labelledby="how">
		<h2 id="how">How it works</h2>
		<ol class="how">
			<li>
				<strong>Share.</strong> Open UnScreen next to your meeting and press Start. Chrome asks which tab or window to read;
				pick the meeting. Your screen reader stays on UnScreen. The presenter installs nothing.
			</li>
			<li>
				<strong>Rebuild.</strong> When the shared screen changes and settles, UnScreen sends one picture to its engine.
				Gemini reads it into rows, columns, lines and headings. A second, independent read checks it, and anything the two
				reads disagree on is marked unclear.
			</li>
			<li>
				<strong>Listen.</strong> Read the result like a web page, with table navigation and headers. Changes are announced
				politely, once ("Acme Corp, Q3 revenue: $1.1M to $1.2M"), and your reading position never jumps.
			</li>
		</ol>
	</section>

	{#if run && o}
		<section aria-labelledby="measured">
			<h2 id="measured">Measured, not claimed</h2>
			<p>
				{o.unscreen.frames} test frames ({kinds.join(', ')}): {variants.join('; ')}. Compared with Tesseract OCR, given
				extra help to find table cells. Run on {date(run.run_at)} with {run.models.reconstruct}{o.errors
					? `; ${o.errors} more frames were not read because the free-tier API quota ran out, and are not counted`
					: ''}.
			</p>
			<table class="numbers">
				<caption class="visually-hidden">UnScreen compared with OCR</caption>
				<thead>
					<tr><th scope="col">Measure</th><th scope="col">UnScreen</th><th scope="col">OCR baseline</th></tr>
				</thead>
				<tbody>
					<tr>
						<th scope="row">Cells and lines read exactly</th>
						<td>{pct(o.unscreen.exact_match)}</td>
						<td>{pct(o.ocr.exact_match)}</td>
					</tr>
					<tr>
						<th scope="row">Wrong but stated as fact</th>
						<td>{pct(o.unscreen.hallucination_rate)}</td>
						<td>{pct(o.ocr.hallucination_rate)}</td>
					</tr>
					<tr>
						<th scope="row">Found values in the right row and column</th>
						<td>{pct(o.unscreen.structure_accuracy)}</td>
						<td>{pct(o.ocr.structure_accuracy)}</td>
					</tr>
				</tbody>
			</table>
			<p><a href={resolve('/(site)/benchmark')}>Full results, method and what failed</a></p>
		</section>
	{/if}

	<section aria-labelledby="privacy">
		<h2 id="privacy">What leaves your computer</h2>
		<p>
			Pictures of the shared screen go to UnScreen's engine and on to Google's Gemini API to be read. UnScreen does not
			store them, and there are no accounts or analytics. <a href={resolve('/(site)/privacy')}>The details</a>.
		</p>
	</section>
</main>

<style>
	.landing {
		display: grid;
		gap: clamp(2.5rem, 6vw, 4.5rem);
		padding-top: clamp(2rem, 6vw, 4rem);
	}
	.intro h1 {
		font-size: clamp(var(--s3), 6vw, var(--s5));
		max-width: 17ch;
		margin-bottom: 0.6em;
	}
	.lead {
		font-size: var(--s1);
		max-width: 60ch;
	}
	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem 1.5rem;
		align-items: center;
		margin-top: 1.5rem;
	}
	section > h2 {
		font-size: var(--s3);
	}
	.how {
		max-width: var(--measure);
		padding-left: 1.4em;
	}
	.how li {
		margin-bottom: 0.9em;
		padding-left: 0.3em;
	}
	.how li::marker {
		font-weight: 800;
	}
	.numbers {
		border-collapse: collapse;
		margin-block: 1rem;
		font-size: var(--s1);
	}
	.numbers th,
	.numbers td {
		text-align: start;
		padding: 0.5em 1.4em 0.5em 0;
		border-bottom: 1px solid var(--rule);
	}
	.numbers thead th {
		border-bottom: 2px solid var(--ink);
		font-size: var(--s0);
	}
	.numbers tbody th {
		font-weight: 400;
	}
	.numbers td:nth-child(2) {
		font-weight: 800;
	}
	@media (max-width: 520px) {
		.numbers {
			font-size: var(--s0);
		}
	}
</style>
