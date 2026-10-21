<script lang="ts">
	import { bench, date, pct, secs, type Aggregate, type Run } from '#lib/bench/format.ts';

	const runs: { title: string; run: Run }[] = [];
	if (bench.full) runs.push({ title: 'Full benchmark', run: bench.full });
	if (bench.kill) runs.push({ title: 'Kill test: 10 spreadsheets in a meeting window', run: bench.kill });

	const groupName = (g: string) => {
		const [kind, variant] = g.split('/');
		const k = { sheet: 'Spreadsheets', code: 'Code', slide: 'Slides and documents' }[kind] ?? kind;
		const v = { '720p': '720p', '1080p': '1080p', '1080p-degraded': 'meeting window, 720p, lossy' }[variant] ?? variant;
		return `${k}, ${v}`;
	};
	const done = (a: Aggregate) => `${a.unscreen.frames} of ${a.unscreen.frames + a.errors}`;
</script>

<svelte:head>
	<title>Benchmark | UnScreen</title>
	<meta name="description" content="How accurately UnScreen rebuilds shared screens, compared with OCR, with method and failures." />
</svelte:head>

<main id="main" class="wrap bench">
	<h1>Benchmark</h1>
	<p>
		Every number on this page is measured, generated from the result files in
		<code>bench/results</code>. Frames that failed to come back from the API are reported, not hidden.
	</p>

	{#each runs as { title, run } (run.file)}
		<section aria-labelledby="h-{run.file}">
			<h2 id="h-{run.file}">{title}</h2>
			<p class="meta">
				Run {date(run.run_at)}. Reads by {run.models.reconstruct}; {run.models.cross_check
					? `every read cross-checked by ${run.models.verify}`
					: 'no cross-check read (it was added after this run)'}; image resolution {run.models.image_resolution}. Source:
				<code>{run.file}</code>.
			</p>
			<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
			<div class="scroll" role="region" aria-label="{title}, results table, scrollable" tabindex="0">
				<table>
					<caption class="visually-hidden">{title}: UnScreen and OCR by content type</caption>
					<thead>
						<tr>
							<th scope="col">Frames</th>
							<th scope="col">Read</th>
							<th scope="col">Exact, UnScreen</th>
							<th scope="col">Exact, OCR</th>
							<th scope="col">Wrong as fact, UnScreen</th>
							<th scope="col">Wrong as fact, OCR</th>
							<th scope="col">Right place, UnScreen</th>
							<th scope="col">Right place, OCR</th>
							<th scope="col">Character errors, UnScreen</th>
						</tr>
					</thead>
					<tbody>
						{#each Object.entries(run.groups) as [g, a] (g)}
							<tr>
								<th scope="row">{groupName(g)}</th>
								<td>{done(a)}</td>
								<td>{pct(a.unscreen.exact_match)}</td>
								<td>{pct(a.ocr.exact_match)}</td>
								<td>{pct(a.unscreen.hallucination_rate)}</td>
								<td>{pct(a.ocr.hallucination_rate)}</td>
								<td>{pct(a.unscreen.structure_accuracy)}</td>
								<td>{pct(a.ocr.structure_accuracy)}</td>
								<td>{pct(a.unscreen.cer, 2)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<p>
				Reconstruction time per frame: median {secs(run.overall.latency_ms.p50)}, 95th percentile
				{secs(run.overall.latency_ms.p95)}. Cost per frame: {run.overall.cost_usd_per_frame === null
					? 'not measured'
					: `$${run.overall.cost_usd_per_frame.toFixed(4)}`}, from token counts and Google's published prices.
			</p>
		</section>
	{/each}

	{#if bench.pipeline}
		<section aria-labelledby="overhead">
			<h2 id="overhead">UnScreen's own latency</h2>
			<p>
				With a scripted model that answers instantly, an edit in a live spreadsheet is spoken
				<strong>{secs(bench.pipeline.p50_ms)}</strong> later (median of {bench.pipeline.edits} edits, longest
				{secs(bench.pipeline.max_ms)}). That time is the 500 ms capture interval, the 300 ms wait for the screen to settle,
				the engine's own processing and the 1.5 s window that groups changes into one announcement. Everything beyond it is
				the vision model. Source: <code>{bench.pipeline.file}</code>.
			</p>
		</section>
	{/if}

	{#if bench.live?.length}
		<section aria-labelledby="live">
			<h2 id="live">Live loop</h2>
			<p>
				The real reader app watching a scripted spreadsheet that edits itself, through the real engine and the Gemini API.
				Changes come from the fixture's own record of what it edited.
			</p>
			<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
			<div class="scroll" role="region" aria-label="Live loop runs, scrollable" tabindex="0">
			<table>
				<caption class="visually-hidden">Live loop runs</caption>
				<thead>
					<tr>
						<th scope="col">Run</th>
						<th scope="col">Edits</th>
						<th scope="col">Announced (recall)</th>
						<th scope="col">Announcements that were real changes (precision)</th>
						<th scope="col">Change to announcement, median</th>
						<th scope="col">Final table matches</th>
					</tr>
				</thead>
				<tbody>
					{#each bench.live as l (l.file)}
						<tr>
							<th scope="row">{date(l.run_at)}, {l.kind}{l.never_read ? ': no frame read, the API was rate limiting' : ''}</th>
							<td>{l.truth_changes}</td>
							<td>{pct(l.recall)}</td>
							<td>{pct(l.precision)}</td>
							<td>{secs(l.change_to_announce_ms.p50)}</td>
							<td>{l.final_dom_vs_truth ? `${l.final_dom_vs_truth.ok} of ${l.final_dom_vs_truth.total} cells` : 'not measured'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
			</div>
		</section>
	{/if}

	<section aria-labelledby="method">
		<h2 id="method">Method</h2>
		<ul>
			<li>
				<strong>Frames.</strong> 40 generated fixtures: 20 spreadsheets in six layouts, 10 code files in four languages, and 10
				slides or documents. Each is captured at 720p and 1080p, and inside a meeting window downscaled to 720p and saved as
				JPEG at quality 50–70 to mimic a meeting codec. Each fixture records exactly what it shows.
			</li>
			<li><strong>Exact:</strong> share of true cells, lines or blocks whose text matches after whitespace is normalised.</li>
			<li>
				<strong>Wrong as fact:</strong> of everything stated without an "unclear" or "unreadable" flag, the share that is
				wrong or does not exist. This is the number UnScreen is built to keep near zero.
			</li>
			<li>
				<strong>Right place:</strong> of the true values that appear anywhere in the output, the share that sits in the right
				row and column, or line.
			</li>
			<li>
				<strong>OCR baseline:</strong> Tesseract 5.5 in three settings, with the best one reported. Its words are grouped into
				cells at wide gaps and its header row is chosen with the help of the true headers. Screen reader OCR does neither,
				so this baseline is generous.
			</li>
		</ul>
	</section>

	<section aria-labelledby="failed">
		<h2 id="failed">What failed</h2>
		<ul>
			<li>
				<strong>Speed.</strong> The target was an announcement within 3.5 seconds of a change. The times measured with
				Gemini are tens of seconds, but they are not the model's speed: the key used was on Gemini's free tier, which allows
				20 requests per day per model. Calls refused with HTTP 429 were retried with backoff, and that waiting is counted.
				Without the model, UnScreen's own share is shown above.
			</li>
			<li>
				<strong>Some frames were never read</strong> because the daily free-tier quota ran out mid-run. They are counted above
				as not read. The full benchmark across code, slides and all resolutions needs about 240 model calls and was not run on
				the free tier.
			</li>
			<li>
				<strong>Digits in compressed video.</strong> On one frame, 4 of 105 cells had a digit misread (6 and 8, 9 and 3). A
				second independent read now flags most such cells as unclear, but it did not catch every one.
			</li>
		</ul>
	</section>
</main>

<style>
	.bench {
		padding-top: 2rem;
	}
	.bench h2 {
		margin-top: 2.5rem;
	}
	.meta {
		color: var(--ink-soft);
	}
	.scroll {
		overflow-x: auto;
		max-width: 100%;
	}
	table {
		border-collapse: collapse;
		margin-block: 1rem;
	}
	th,
	td {
		text-align: start;
		padding: 0.45em 1em 0.45em 0;
		border-bottom: 1px solid var(--rule);
		vertical-align: top;
	}
	thead th {
		border-bottom: 2px solid var(--ink);
		font-size: var(--s-1);
	}
	tbody th {
		font-weight: 700;
		white-space: nowrap;
	}
	ul {
		max-width: var(--measure);
		padding-left: 1.2em;
	}
	li {
		margin-bottom: 0.6em;
	}
	code {
		font-family: var(--font-mono);
		font-size: 0.9em;
	}
</style>
