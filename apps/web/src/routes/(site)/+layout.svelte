<script lang="ts">
	import { page } from '$app/state';
	import Wordmark from '#lib/site/Wordmark.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const links = [
		{ href: '/app', label: 'Reader' },
		{ href: '/help', label: 'Help and shortcuts' },
		{ href: '/benchmark', label: 'Benchmark' },
		{ href: '/privacy', label: 'Privacy' }
	];
</script>

<a class="skip" href="#main">Skip to content</a>
<header class="site wrap">
	<a href="/" class="home" aria-label="UnScreen home"><Wordmark /></a>
	<nav aria-label="Site">
		<ul>
			{#each links as l (l.href)}
				<li><a href={l.href} aria-current={page.url.pathname === l.href ? 'page' : undefined}>{l.label}</a></li>
			{/each}
		</ul>
	</nav>
</header>

{@render children()}

<footer class="site-foot wrap">
	<p>
		UnScreen is a student project built for the Taskforge hackathon, October 2026. Shared frames are sent to Google's
		Gemini API to be read and are not stored by UnScreen. <a href="/privacy">How your screen is handled</a>.
	</p>
	<p><a href="https://github.com/rahulgunwanistudy-2005/unscreen">Source code on GitHub</a></p>
</footer>

<style>
	.site {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem 2rem;
		padding-block: 1.1rem;
		border-bottom: 2px solid var(--ink);
	}
	.home {
		text-decoration: none;
	}
	nav ul {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 1.4rem;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	nav a {
		font-weight: 700;
		text-decoration: none;
		padding-block: 0.4rem;
		display: inline-block;
	}
	nav a:hover,
	nav a[aria-current='page'] {
		text-decoration: underline;
		text-decoration-thickness: 0.18em;
		text-underline-offset: 0.3em;
	}
	.site-foot {
		margin-top: 5rem;
		padding-block: 2rem 3rem;
		border-top: 2px solid var(--ink);
		color: var(--ink-soft);
		font-size: var(--s-1);
	}
</style>
