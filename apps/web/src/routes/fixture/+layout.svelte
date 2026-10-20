<script lang="ts">
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<meta name="robots" content="noindex" />
</svelte:head>

{@render children()}

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		overflow: hidden;
	}
</style>
