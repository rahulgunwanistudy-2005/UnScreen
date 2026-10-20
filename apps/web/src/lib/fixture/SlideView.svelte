<script lang="ts">
	import type { SlideFixture } from './slide.ts';

	let { slide }: { slide: SlideFixture } = $props();
</script>

{#if slide.kind === 'slide'}
	<div class="slide {slide.theme}">
		{#each slide.blocks as block, i (i)}
			{#if block.kind === 'heading'}
				<div class="title" data-truth="b{i}">{block.text}</div>
			{:else}
				<div class="bullet" data-truth="b{i}">{block.text}</div>
			{/if}
		{/each}
		<div class="foot" aria-hidden="true">{slide.seed % 20 + 3}</div>
	</div>
{:else}
	<div class="doc">
		<div class="page">
			{#each slide.blocks as block, i (i)}
				{#if block.kind === 'heading'}
					<div class="h h{block.level}" data-truth="b{i}">{block.text}</div>
				{:else if block.kind === 'list_item'}
					<div class="li" data-truth="b{i}">{block.text}</div>
				{:else}
					<div class="p" data-truth="b{i}">{block.text}</div>
				{/if}
			{/each}
		</div>
	</div>
{/if}

<style>
	.slide {
		width: 100%;
		height: 100%;
		box-sizing: border-box;
		padding: 7% 9%;
		font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
		position: relative;
	}
	.light {
		background: #ffffff;
		color: #1b1b1b;
	}
	.dark {
		background: #14213d;
		color: #f1f1f1;
	}
	.accent {
		background: linear-gradient(135deg, #fde68a, #fca5a5);
		color: #111;
	}
	.title {
		font-size: 4.2cqmin;
		font-weight: bold;
		margin-bottom: 5cqmin;
	}
	.bullet {
		font-size: 2.8cqmin;
		margin: 2.2cqmin 0 0 3cqmin;
		position: relative;
	}
	.bullet::before {
		content: '';
		position: absolute;
		left: -2.4cqmin;
		top: 1.1cqmin;
		width: 1cqmin;
		height: 1cqmin;
		border-radius: 50%;
		background: currentColor;
	}
	.foot {
		position: absolute;
		right: 4%;
		bottom: 4%;
		font-size: 1.8cqmin;
		opacity: 0.6;
	}
	.doc {
		width: 100%;
		height: 100%;
		background: #f1f3f4;
		display: flex;
		justify-content: center;
		overflow: hidden;
	}
	.page {
		width: 62%;
		margin-top: 3%;
		background: #fff;
		color: #202124;
		padding: 5% 7%;
		font-family: Georgia, 'Times New Roman', serif;
		font-size: 2cqmin;
		line-height: 1.5;
	}
	.h1 {
		font-size: 3.4cqmin;
		font-weight: bold;
		margin-bottom: 2cqmin;
	}
	.h2 {
		font-size: 2.6cqmin;
		font-weight: bold;
		margin: 2.4cqmin 0 1cqmin;
	}
	.p {
		margin-bottom: 1.4cqmin;
	}
	.li {
		margin-left: 3cqmin;
		display: list-item;
		list-style: disc;
	}
</style>
