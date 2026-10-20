<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		enabled,
		presenter = 'Asha Rao',
		children
	}: { enabled: boolean; presenter?: string; children: Snippet } = $props();

	const participants = ['AR', 'BO', 'CW', 'DM'];
	let shareWidth = $state(1152);
</script>

{#if enabled}
	<div class="meet">
		<div class="stage">
			<div class="label">{presenter} is presenting</div>
			<div class="share" data-truth="content" bind:clientWidth={shareWidth}>
				<div class="inner" style:transform="scale({shareWidth / 1920})">{@render children()}</div>
			</div>
		</div>
		<aside class="people" aria-hidden="true">
			{#each participants as p (p)}
				<div class="tile"><span>{p}</span></div>
			{/each}
		</aside>
		<div class="bar" aria-hidden="true">
			<span class="clock">10:42 | Weekly sync</span>
			<span class="btn"></span><span class="btn"></span><span class="btn"></span>
			<span class="btn leave"></span>
		</div>
	</div>
{:else}
	<div class="plain" data-truth="content">{@render children()}</div>
{/if}

<style>
	.plain {
		width: 100vw;
		height: 100vh;
		overflow: hidden;
		position: relative;
		container-type: size;
	}
	.meet {
		width: 100vw;
		height: 100vh;
		background: #202124;
		display: grid;
		grid-template-columns: 1fr 15vw;
		grid-template-rows: 1fr 9vh;
		gap: 1vw;
		padding: 1.2vw;
		box-sizing: border-box;
		font-family: Arial, sans-serif;
		color: #e8eaed;
	}
	.stage {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 0;
	}
	.label {
		position: absolute;
		left: 0.6vw;
		bottom: 0.4vw;
		font-size: 1vw;
		background: rgb(0 0 0 / 0.55);
		padding: 0.2vw 0.6vw;
		border-radius: 0.3vw;
		z-index: 2;
	}
	.share {
		aspect-ratio: 16 / 9;
		width: min(100%, calc((100vh - 9vh - 3.4vw) * 16 / 9));
		overflow: hidden;
		border-radius: 0.4vw;
		background: #fff;
	}
	.inner {
		width: 1920px;
		height: 1080px;
		transform-origin: 0 0;
		position: relative;
		container-type: size;
	}
	.people {
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 0.8vw;
	}
	.tile {
		aspect-ratio: 16 / 10;
		background: #3c4043;
		border-radius: 0.5vw;
		display: grid;
		place-items: center;
	}
	.tile span {
		width: 4vw;
		height: 4vw;
		border-radius: 50%;
		background: #5f6368;
		display: grid;
		place-items: center;
		font-size: 1.4vw;
	}
	.bar {
		grid-column: 1 / -1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1vw;
		position: relative;
	}
	.clock {
		position: absolute;
		left: 0.5vw;
		font-size: 1.1vw;
	}
	.btn {
		width: 3.2vw;
		height: 3.2vw;
		border-radius: 50%;
		background: #3c4043;
	}
	.leave {
		width: 5vw;
		border-radius: 1.6vw;
		background: #ea4335;
	}
</style>
