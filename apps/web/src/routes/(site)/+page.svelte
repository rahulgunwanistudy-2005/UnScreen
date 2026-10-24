<script lang="ts">
	import { resolve } from '$app/paths';
	import { withQuery } from '#lib/site/href.ts';
	import { date, headline, pct } from '#lib/bench/format.ts';
	import Globe from '#lib/hero/Globe.svelte';
	import Hero from '#lib/hero/Hero.svelte';
	import Icon from '#lib/site/Icon.svelte';

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

<main id="main" class="landing">
 <section class="intro" aria-labelledby="title">
  <div class="horizon" aria-hidden="true"></div>
  <div class="globe"><Globe /></div>
  <div class="intro-inner wrap">
   <div class="intro-copy">
    <p class="intro-note"><span></span> A clearer way to follow along</p>
    <h1 id="title">Every screen share.<br />Readable, live.</h1>
    <p class="lead">Turn a shared screen into a table, code or text your screen reader can navigate. Stay with the conversation, even as the screen changes.</p>
    <div class="actions">
     <a class="button" href={resolve('/(site)/app')}><Icon name="spark" size={18} /> Start reading a shared screen</a>
     <a class="button quiet" href="#in-action"><Icon name="play" size={16} /> See it in action</a>
    </div>
    <ul class="intro-benefits">
     <li><Icon name="check" size={15} /> No presenter setup</li>
     <li><Icon name="check" size={15} /> Your screen reader, your pace</li>
     <li><Icon name="check" size={15} /> No account needed</li>
    </ul>
   </div>
   <div class="orbit-note" aria-hidden="true"><span class="orbit-icon"><Icon name="screen" size={23} /></span><div>From pixels to understanding.<small>Tables. Code. Slides. One readable space.</small></div></div>
  </div>
 </section>

 <div class="compatibility wrap">
  <p>Works alongside your meeting</p>
  <ul><li>zoom<span class="meeting-dot"></span></li><li><Icon name="screen" size={22} /> Google Meet</li><li><span class="teams-mark" aria-hidden="true">T</span> Microsoft Teams</li></ul>
  <span class="compat-note">Built for NVDA, VoiceOver &amp; ChromeVox</span>
 </div>

 <div class="landing-body wrap">
  <section id="in-action" class="demo-section" aria-labelledby="demo-title">
   <div class="section-heading"><div><p class="section-note">The screen, made accessible</p><h2 id="demo-title">A picture becomes a place<br />you can move through.</h2></div><p>Real rows. Real headers. Your place stays put.<br />Explore a generated sheet rebuilt by the real model.</p></div>
   <Hero />
   <a class="sample-link" href={withQuery(resolve('/fixture/sheet'), 'seed=1')} target="_blank" rel="noopener">Open a test spreadsheet to share (new tab) <Icon name="arrow" size={16} /></a>
  </section>

	<section class="barrier-section" aria-labelledby="problem">
   <div class="barrier-heading"><span class="feature-icon"><Icon name="screen" size={26} /></span>
		<h2 id="problem">Screen sharing should<br />include everyone.</h2></div>
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

	<section class="how-section" aria-labelledby="how">
   <p class="section-note">A simpler way to stay in the meeting</p>
		<h2 id="how">Share. Rebuild. Listen.</h2>
		<ol class="how">
			<li>
				<span class="step-icon"><Icon name="screen" size={25} /></span><h3>Share the meeting.</h3> Open UnScreen next to your meeting and press Start. Chrome asks which tab or window to read;
				pick the meeting. Your screen reader stays on UnScreen. The presenter installs nothing.
			</li>
			<li>
				<span class="step-icon"><Icon name="table" size={25} /></span><h3>Make it readable.</h3> When the shared screen changes and settles, UnScreen sends one picture to its engine.
				Gemini reads it into rows, columns, lines and headings. A second, independent read checks it, and anything the two
				reads disagree on is marked unclear.
			</li>
			<li>
				<span class="step-icon"><Icon name="sound" size={25} /></span><h3>Follow every change.</h3> Read the result like a web page, with table navigation and headers. Changes are announced
				politely, once ("Acme Corp, Q3 revenue: $1.1M to $1.2M"), and your reading position never jumps.
			</li>
		</ol>
	</section>

	{#if run && o}
		<section class="measured-section" aria-labelledby="measured">
    <p class="section-note">Transparency, at every step</p>
			<h2 id="measured">Measured, not claimed</h2>
			<p>
				{o.unscreen.frames} test frames ({kinds.join(', ')}): {variants.join('; ')}. Compared with Tesseract OCR, given
				extra help to find table cells. Run on {date(run.run_at)} with {run.models.reconstruct}{o.errors
					? `; ${o.errors} more frames failed and are listed on the benchmark page; accuracy covers completed frames`
					: ''}.
			</p>
			<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
			<div class="metrics-scroll" role="region" aria-label="UnScreen compared with OCR, scrollable" tabindex="0">
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
			</div>
			<p><a href={resolve('/(site)/benchmark')}>Full results, method and what failed</a></p>
		</section>
	{/if}

	<section class="privacy-section" aria-labelledby="privacy">
   <div><span class="feature-icon"><Icon name="shield" size={25} /></span>
		<h2 id="privacy">Your screen. Your choice.</h2></div>
		<p>
			Pictures of the shared screen go to UnScreen's engine and on to Google's Gemini API to be read. UnScreen does not
			store them, and there are no accounts or analytics. <a href={resolve('/(site)/privacy')}>The details</a>.
		</p>
	</section>
 <section class="closing" aria-labelledby="closing-title"><Icon name="screen" size={34} /><h2 id="closing-title">Be part of the conversation.</h2><p>Your next screen share can be a little more accessible.</p><a class="button" href={resolve('/(site)/app')}>Open the reader <Icon name="arrow" size={18} /></a></section>
 </div>
</main>

<style>
	.landing {
		overflow-x: clip;
	}
	.intro {
		position: relative;
		isolation: isolate;
		/* The globe rises behind the site header but stops at the bottom of the scene. */
		clip-path: inset(-14rem 0 0 0);
		min-height: 42rem;
		color: #f2f7ff;
		background: #030713;
	}
	.intro-inner {
		position: relative;
		min-height: inherit;
		padding-block: 5.2rem 5.5rem;
	}
	.intro-copy {
		position: relative;
		z-index: 2;
		max-width: 37rem;
	}
	.intro-note {
		display: flex;
		align-items: center;
		gap: .6rem;
		font-size: .8rem;
		color: #c0d4ef;
		margin-bottom: 2rem;
	}
	.intro-note span {
		width: .4rem;
		height: .4rem;
		border-radius: 50%;
		background: #b5dcff;
		box-shadow: 0 0 12px #65aefc;
	}
	.intro h1 {
		font-size: clamp(3.2rem, 6.3vw, 5.5rem);
		font-weight: 400;
		line-height: 1.03;
		letter-spacing: -.065em;
		margin-bottom: 1.5rem;
	}
	.lead {
		max-width: 39ch;
		font-size: 1.05rem;
		line-height: 1.65;
		color: #c3d3e8;
	}
	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: .8rem;
		align-items: center;
		margin-top: 2rem;
	}
	.intro .button {
		background: #eef6ff;
		color: #0a1526;
		border-color: #eef6ff;
	}
	.intro .button:hover {
		background: #c2e2ff;
		border-color: #c2e2ff;
	}
	.intro .button.quiet {
		background: rgb(6 20 41 / .65);
		border-color: #5a7699;
		color: #f2f7ff;
	}
	.intro .button.quiet:hover {
		background: #173759;
	}
	.intro-benefits {
		list-style: none;
		margin: 1.8rem 0 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: .65rem 1.2rem;
		font-size: .72rem;
		color: #bccde2;
	}
	.intro-benefits li {
		display: flex;
		align-items: center;
		gap: .4rem;
	}
	.globe {
		--g: min(92vw, 80rem);
		position: absolute;
		z-index: -2;
		width: var(--g);
		/* Anchor to the content column, which stops growing at 88rem. */
		right: calc(max(0px, (100vw - 88rem) / 2) - var(--g) * 0.2);
		top: calc(var(--g) * -0.43);
		pointer-events: none;
	}
	.horizon {
		position: absolute;
		z-index: -1;
		inset: -14rem 0 0;
		background: linear-gradient(90deg, #030713 0%, rgb(3 7 19 / .62) 30%, transparent 52%), linear-gradient(0deg, #050a16, transparent 15%), radial-gradient(ellipse 80% 30% at 75% 87%, #d4ecff 0%, #7dbcf0 22%, #2a63a3 50%, transparent 100%);
	}
	.orbit-note {
		position: absolute;
		right: var(--gutter);
		bottom: 5.5rem;
		display: flex;
		align-items: center;
		gap: .8rem;
		padding: 1rem 1.2rem;
		border: 1px solid #7297be;
		border-radius: 14px;
		background: rgb(5 24 50 / .78);
		font-size: .9rem;
		backdrop-filter: blur(16px);
		box-shadow: 0 15px 50px #03112b;
	}
	.orbit-note {
		max-width: calc(100% - 2 * var(--gutter));
	}
	.orbit-note > div {
		min-width: 0;
	}
	.orbit-note small {
		display: block;
		color: #c4d7ee;
		font-size: .7rem;
		margin-top: .1rem;
	}
	.orbit-icon {
		color: #c0e2ff;
	}
	.compatibility {
		display: flex;
		gap: 1.5rem;
		align-items: center;
		justify-content: space-between;
		padding-block: 2rem;
		border-bottom: 1px solid var(--rule);
	}
	.compatibility p,.compat-note {
		color: var(--ink-soft);
		font-size: .75rem;
		margin: 0;
	}
	.compatibility ul {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 2.3rem;
		align-items: center;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.compatibility li {
		display: flex;
		align-items: center;
		gap: .5rem;
		font-size: 1.1rem;
		font-weight: 500;
		letter-spacing: -.03em;
	}
	.compatibility li:first-child {
		font-size: 1.6rem;
		font-weight: 650;
		letter-spacing: -.08em;
	}
	.meeting-dot {
		width: .35rem;
		height: .35rem;
		border-radius: 50%;
		background: var(--accent);
		align-self: end;
		margin-bottom: .5rem;
	}
	.teams-mark {
		font-size: .85rem;
		background: var(--surface-raised);
		border: 1px solid var(--rule);
		width: 1.5rem;
		height: 1.5rem;
		text-align: center;
		border-radius: 4px;
	}
	.landing-body {
		display: grid;
		gap: 6rem;
		padding-top: 5rem;
	}
	.section-heading {
		display: flex;
		justify-content: space-between;
		align-items: end;
		gap: 2rem;
		margin-bottom: 2rem;
	}
	.section-heading h2,section > h2,.barrier-heading h2,.privacy-section h2 {
		font-size: clamp(1.9rem, 3vw, 2.8rem);
		font-weight: 400;
		letter-spacing: -.045em;
	}
	.section-heading h2 {
		margin: 0;
	}
	.section-heading > p {
		color: var(--ink-soft);
		font-size: .86rem;
		max-width: 32ch;
		margin-bottom: .15rem;
	}
	.section-note {
		color: var(--accent);
		font-size: .8rem;
		margin-bottom: .8rem;
	}
	.demo-section {
		scroll-margin-top: 2rem;
		min-width: 0;
	}
	.sample-link {
		display: inline-flex;
		align-items: center;
		gap: .6rem;
		margin-top: 1.2rem;
		font-size: .8rem;
		color: var(--ink-soft);
	}
	.barrier-section {
		display: grid;
		grid-template-columns: 1fr 1.1fr;
		align-items: center;
		gap: 4rem;
	}
	.barrier-section > p {
		color: var(--ink-soft);
		font-size: .95rem;
		margin: 0;
	}
	.feature-icon,.step-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 3rem;
		height: 3rem;
		border: 1px solid var(--rule);
		background: linear-gradient(140deg, var(--surface-raised), var(--surface));
		color: var(--accent);
		border-radius: 12px;
		margin-bottom: 1.3rem;
	}
	.how-section > h2 {
		margin-bottom: 2rem;
	}
	.how {
		list-style: none;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		padding: 0;
		margin: 0;
		counter-reset: step;
	}
	.how li {
		position: relative;
		padding: 1.8rem;
		border: 1px solid var(--rule);
		border-radius: 18px;
		background: linear-gradient(145deg, var(--surface), var(--paper));
		font-size: .9rem;
		color: var(--ink-soft);
		counter-increment: step;
	}
	.how li::before {
		content: '0' counter(step);
		position: absolute;
		right: 1.5rem;
		top: 1.5rem;
		font-size: .8rem;
		color: var(--ink-soft);
	}
	.how h3 {
		color: var(--ink);
		font-size: 1.3rem;
		font-weight: 500;
	}
	.how .step-icon {
		background: none;
		border: 0;
		justify-content: start;
	}
	.measured-section {
		padding: 2.5rem;
		border: 1px solid var(--rule);
		border-radius: 22px;
		background: radial-gradient(ellipse at 100% 0%, var(--ambient), transparent 65%), var(--surface);
		min-width: 0;
	}
	.measured-section > p {
		color: var(--ink-soft);
		font-size: .9rem;
	}
	.metrics-scroll {
		overflow-x: auto;
		max-width: 100%;
	}
	.numbers {
		width: 100%;
		min-width: 26rem;
		border-collapse: collapse;
		margin-block: 2rem 1.5rem;
		font-size: 1rem;
	}
	.numbers th,.numbers td {
		text-align: start;
		padding: 1em .8em;
		border-bottom: 1px solid var(--rule);
	}
	.numbers thead th {
		font-size: .8rem;
		color: var(--ink-soft);
		font-weight: 500;
	}
	.numbers tbody th {
		font-weight: 400;
	}
	.numbers td:nth-child(2) {
		color: var(--accent);
		font-weight: 600;
		font-size: 1.3rem;
	}
	.privacy-section {
		display: grid;
		grid-template-columns: 1fr 1.1fr;
		gap: 4rem;
		align-items: center;
		padding-bottom: 3rem;
		border-bottom: 1px solid var(--rule);
	}
	.privacy-section > p {
		color: var(--ink-soft);
		margin: 0;
	}
	.closing {
		text-align: center;
		padding: 0 1rem 1rem;
	}
	.closing > :global(svg) {
		color: var(--accent);
		margin-bottom: 1.5rem;
	}
	.closing h2 {
		font-size: clamp(2rem, 4vw, 3.3rem);
	}
	.closing p {
		margin-inline: auto;
		color: var(--ink-soft);
	}
	.closing .button {
		margin-top: .75rem;
	}
	@media (max-width: 1100px) {
		.compat-note {
			display: none;
		}
		.globe {
			--g: 110vw;
			right: calc(var(--g) * -0.36);
			top: calc(var(--g) * -0.36);
		}
		.orbit-note {
			bottom: 3rem;
		}
		.intro-inner {
			padding-block: 4rem 10rem;
		}
		/* Keep the stage light below the benefit list so its text stays legible. */
		.horizon {
			background: linear-gradient(90deg, #030713 0%, rgb(3 7 19 / .62) 30%, transparent 52%), linear-gradient(0deg, #050a16, transparent 15%), radial-gradient(ellipse 80% 24% at 78% 96%, #d4ecff 0%, #7dbcf0 22%, #2a63a3 50%, transparent 100%);
		}
		.intro-copy {
			max-width: 32rem;
		}
		.intro h1 {
			font-size: 4.6rem;
		}
		.how li {
			padding: 1.4rem;
		}
	}
	@media (max-width: 760px) {
		.intro {
			min-height: 45rem;
		}
		.intro-inner {
			padding-block: 3rem 12rem;
		}
		.intro h1 {
			font-size: clamp(3rem, 9vw, 4.5rem);
		}
		.globe {
			--g: 46rem;
			right: calc(var(--g) * -0.5);
			top: calc(var(--g) * -0.3);
			opacity: .9;
		}
		.horizon {
			background: linear-gradient(90deg, #030713 0%, rgb(3 7 19 / .7) 55%, transparent), linear-gradient(0deg, #050a16, transparent 18%), radial-gradient(ellipse 100% 25% at 85% 88%, #a4d5fa, #23598d 60%, transparent);
		}
		.orbit-note {
			left: var(--gutter);
			right: auto;
			bottom: 3.5rem;
		}
		.compatibility {
			flex-direction: column;
			gap: 1rem;
			padding-block: 1.5rem;
		}
		.compatibility ul {
			gap: 1.3rem;
		}
		.compatibility li {
			font-size: .9rem;
		}
		.compatibility li:first-child {
			font-size: 1.3rem;
		}
		.landing-body {
			gap: 4rem;
			padding-top: 3rem;
		}
		.section-heading {
			align-items: start;
			flex-direction: column;
			gap: 1rem;
		}
		.section-heading > p {
			max-width: 45ch;
		}
		.barrier-section,.privacy-section {
			grid-template-columns: 1fr;
			gap: 1rem;
		}
		.how {
			grid-template-columns: 1fr;
		}
		.measured-section {
			padding: 1.3rem;
		}
		.numbers {
			font-size: .8rem;
		}
		.numbers th,.numbers td {
			padding: .7em .35em;
		}
		.numbers td:nth-child(2) {
			font-size: 1rem;
		}
	}
	@media (max-width: 420px) {
		.intro-benefits {
			max-width: 28ch;
		}
		.actions {
			align-items: start;
			flex-direction: column;
		}
		.compatibility ul {
			gap: .8rem;
		}
		.compatibility li {
			font-size: .75rem;
		}
		.orbit-note {
			font-size: .8rem;
			padding: .8rem;
		}
		.orbit-note small {
			font-size: .65rem;
		}
		:global(:root[data-large-print='true']) .intro h1 {
			font-size: 2.3rem;
		}
	}
</style>
