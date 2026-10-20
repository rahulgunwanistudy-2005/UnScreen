<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { prefs } from '#lib/a11y/settings.svelte.ts';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(() => prefs.init());
</script>

{@render children()}
