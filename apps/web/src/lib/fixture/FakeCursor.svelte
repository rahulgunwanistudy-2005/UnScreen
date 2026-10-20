<script lang="ts">
	let { x, y }: { x: number; y: number } = $props();
</script>

<svg class="cursor" style:left="{x}%" style:top="{y}%" width="22" height="30" viewBox="0 0 22 30" aria-hidden="true">
	<path d="M1 1 L1 25 L7 19 L11 29 L15 27 L11 18 L20 18 Z" fill="#000" stroke="#fff" stroke-width="1.6" />
</svg>

<style>
	.cursor {
		position: absolute;
		pointer-events: none;
		z-index: 10;
	}
</style>
