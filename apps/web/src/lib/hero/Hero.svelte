<script lang="ts">
	import { onMount } from 'svelte';
	import hero from './hero.json';

	type Phase = 'dots' | 'resolving' | 'done';

	const cells = [
		...hero.columns.map((c, j) => ({ ...c, header: true, row: 0, col: j })),
		...hero.rows.flatMap((r, i) => r.cells.map((c, j) => ({ ...c, header: false, row: i + 1, col: j })))
	];
	const STEP_MS = 55;

	let phase = $state<Phase>('dots');
	let shown = $state(0);
	let canvas: HTMLCanvasElement;
	let timer: ReturnType<typeof setTimeout> | null = null;
	let reduced = $state(false);

	const speech = $derived.by(() => {
		const lines = [{ who: 'UnScreen', text: hero.announcement }];
		if (phase !== 'done') return lines;
		const [c1, c2] = [hero.columns[1].text, hero.columns[2].text];
		const r1 = hero.rows[0];
		const r2 = hero.rows[1];
		lines.push(
			{ who: 'Ctrl+Alt+Right', text: `${c1}, ${r1.cells[1].text}` },
			{ who: 'Ctrl+Alt+Right', text: `${c2}, ${r1.cells[2].text}` },
			{ who: 'Ctrl+Alt+Down', text: `${r2.cells[0].text}, ${r2.cells[2].text}` }
		);
		return lines;
	});

	function drawDots() {
		const ctx = canvas?.getContext('2d');
		if (!ctx) return;
		const img = new Image();
		img.src = hero.image.src;
		img.onload = () => {
			const w = canvas.width;
			const h = canvas.height;
			const step = 9;
			const cols = Math.ceil(w / step);
			const rows = Math.ceil(h / step);
			const small = document.createElement('canvas');
			small.width = cols;
			small.height = rows;
			const sctx = small.getContext('2d', { willReadFrequently: true })!;
			sctx.drawImage(img, 0, 0, cols, rows);
			const px = sctx.getImageData(0, 0, cols, rows).data;
			const style = getComputedStyle(canvas);
			ctx.clearRect(0, 0, w, h);
			for (let y = 0; y < rows; y++) {
				for (let x = 0; x < cols; x++) {
					const i = (y * cols + x) * 4;
					const lum = (px[i] * 0.3 + px[i + 1] * 0.59 + px[i + 2] * 0.11) / 255;
					const r = Math.pow(1 - lum, 0.75) * step * 0.5 + 0.9;
					ctx.fillStyle = style.getPropertyValue('--dot');
					ctx.beginPath();
					ctx.arc(x * step + step / 2, y * step + step / 2, r, 0, Math.PI * 2);
					ctx.fill();
				}
			}
		};
	}

	function stop() {
		if (timer) clearTimeout(timer);
		timer = null;
	}

	function play() {
		stop();
		phase = 'dots';
		shown = 0;
		drawDots();
		timer = setTimeout(function tick() {
			phase = 'resolving';
			shown += 1;
			if (shown >= cells.length) {
				timer = setTimeout(() => (phase = 'done'), 700);
				return;
			}
			timer = setTimeout(tick, STEP_MS);
		}, 1100);
	}

	function finish() {
		stop();
		shown = cells.length;
		phase = 'done';
	}

	onMount(() => {
		const scale = Math.min(3, window.devicePixelRatio || 1);
		canvas.width = hero.image.width * 3 * scale;
		canvas.height = hero.image.height * 3 * scale;
		reduced =
			window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
			document.documentElement.dataset.motion === 'reduce';
		drawDots();
		if (reduced) finish();
		else play();
		return stop;
	});
</script>

<figure class="hero" aria-labelledby="hero-caption">
	<div class="preview-window">
 <div class="window-bar" aria-hidden="true"><div class="window-dots"><i></i><i></i><i></i></div><span>UnScreen / reconstructed content</span><span class="window-type">Spreadsheet</span></div>
 <div class="preview-content">
 <div class="stage" class:done={phase === 'done'} style:aspect-ratio="{hero.image.width} / {hero.image.height}">
		<div class="layer" aria-hidden="true">
			<canvas bind:this={canvas}></canvas>
			{#each cells as c, k (k)}
				<span
					class="cell"
					class:on={k < shown}
					class:head={c.header}
					style:left="{c.box.x * 100}%"
					style:top="{c.box.y * 100}%"
					style:width="{c.box.w * 100}%"
					style:height="{c.box.h * 100}%">{c.text}</span
				>
			{/each}
		</div>
		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div
			class="final"
			class:visually-hidden={phase !== 'done'}
			class:scrolls={phase === 'done'}
			role="region"
			aria-label="Rebuilt table, scrollable"
			tabindex={phase === 'done' ? 0 : undefined}
		>
			<table>
				<caption>{hero.title}, {hero.rows.length} rows, {hero.columns.length} columns</caption>
				<thead>
					<tr>
						{#each hero.columns as col (col.text)}<th scope="col">{col.text}</th>{/each}
					</tr>
				</thead>
				<tbody>
					{#each hero.rows as row, i (i)}
						<tr>
							{#each row.cells as cell, j (j)}
								{#if j === 0}<th scope="row">{cell.text}</th>{:else}<td>{cell.text}</td>{/if}
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	<div class="speech" aria-hidden="true">
		<p class="speech-title">Speech, as text</p>
		<ol>
			{#each speech as line, i (i)}
				<li><span class="who">{line.who}</span> {line.text}</li>
			{/each}
		</ol>
	</div>

 </div>
 </div>
	<figcaption id="hero-caption">
		<span>
			A generated spreadsheet in a simulated meeting window, read by the real model after lossy compression at 720p.
			UnScreen rebuilt every cell in the right place. The first spoken line is its real announcement; the others show
			what the table's headers let a screen reader say as you move.
		</span>
		<button type="button" class="button quiet replay" onclick={() => (phase === 'done' ? play() : finish())}>
			{phase === 'done' ? 'Play the animation' : 'Skip to the table'}
		</button>
	</figcaption>
</figure>

<style>
	.preview-window {
		border: 1px solid var(--rule);
		border-radius: 20px;
		overflow: hidden;
		background: var(--surface);
		box-shadow: var(--shadow), 0 0 90px var(--ambient);
	}
	.window-bar {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: .9rem 1.3rem;
		border-bottom: 1px solid var(--rule);
		font-size: .7rem;
		color: var(--ink-soft);
	}
	.window-dots {
		display: flex;
		gap: 5px;
	}
	.window-dots i {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--mosaic);
	}
	.window-type {
		margin-left: auto;
		color: var(--accent);
		background: var(--surface-raised);
		border: 1px solid var(--rule);
		border-radius: 30px;
		padding: .1rem .6rem;
	}
	.preview-content {
		padding: 1.3rem;
		display: grid;
		grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr);
		gap: 1rem;
		align-items: start;
	}
	@media (max-width: 900px) {
		.preview-content {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 520px) {
		.preview-content {
			padding: .7rem;
		}
		.window-type {
			display: none;
		}
		.window-bar {
			padding: .8rem;
			font-size: .65rem;
		}
	}
	.hero {
		margin: 0;
		display: grid;
		gap: 1rem;
	}
	.stage {
		position: relative;
		width: 100%;
		max-width: 64rem;
		border: 1px solid var(--rule);
		border-radius: 12px;
		background: var(--surface);
		--dot: var(--ink);
		overflow: hidden;
	}
	.layer {
		position: absolute;
		inset: 0;
		transition: opacity 400ms ease;
	}
	.stage.done {
		aspect-ratio: auto !important;
	}
	.stage.done .layer {
		opacity: 0;
	}
	.stage.done .final {
		position: relative;
	}
	canvas {
		width: 100%;
		height: 100%;
		display: block;
	}
	.cell {
		position: absolute;
		display: flex;
		align-items: center;
		padding-inline: 0.4em;
		box-sizing: border-box;
		font-size: clamp(0.5rem, 1.35vw, 0.95rem);
		white-space: nowrap;
		overflow: hidden;
		background: var(--paper);
		color: var(--ink);
		border-bottom: 1px solid var(--rule);
		visibility: hidden;
	}
	.cell.head {
		font-weight: 600;
		border-bottom: 2px solid var(--ink);
	}
	.cell.on {
		visibility: visible;
		animation: flash 900ms ease-out;
	}
	@keyframes flash {
		from {
			box-shadow: inset 0 0 0 3px var(--signal);
		}
		to {
			box-shadow: inset 0 0 0 0 var(--signal);
		}
	}
	.final {
		position: absolute;
		inset: 0;
		overflow: hidden;
		padding: clamp(0.5rem, 2vw, 1.5rem);
		box-sizing: border-box;
	}
	.final.scrolls {
		overflow: auto;
	}
	.final table {
		border-collapse: collapse;
		width: 100%;
		font-size: clamp(0.62rem, 1vw, .85rem);
	}
	.final caption {
		text-align: start;
		font-weight: 700;
		color: var(--ink-soft);
		padding-bottom: 0.4em;
	}
	.final th, .final td {
		text-align: start;
		padding: 0.5em 0.6em;
		border-bottom: 1px solid var(--rule);
		white-space: nowrap;
	}
	.final thead th {
		border-bottom: 2px solid var(--ink);
		font-weight: 600;
	}
	.speech {
		max-width: 64rem;
		font-family: var(--font-mono);
		font-size: var(--s-1);
		border: 1px solid var(--rule);
		border-radius: 12px;
		background: var(--surface-raised);
		padding: 1.3rem;
		align-self: stretch;
	}
	.speech-title {
		color: var(--accent);
		font-family: var(--font-body);
		font-weight: 700;
		margin-bottom: 0.3em;
	}
	.speech ol {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.speech li {
		padding-block: 0.65em;
		border-bottom: 1px solid var(--rule);
	}
	.who {
		display: inline-block;
		min-width: 15ch;
		font-size: .7rem;
		color: var(--ink-soft);
	}
	figcaption {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		align-items: center;
		max-width: 64rem;
		color: var(--ink-soft);
		font-size: var(--s-1);
	}
	figcaption span {
		flex: 1 1 28rem;
	}
	@media (max-width: 520px) {
		.who {
			display: block;
		}
	}
</style>
