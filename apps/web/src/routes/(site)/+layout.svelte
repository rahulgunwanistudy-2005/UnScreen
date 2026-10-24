<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import Wordmark from '#lib/site/Wordmark.svelte';
	import Icon from '#lib/site/Icon.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const links = [
		{ path: '/app', href: resolve('/(site)/app'), label: 'Reader' },
		{ path: '/help', href: resolve('/(site)/help'), label: 'Help and shortcuts' },
		{ path: '/benchmark', href: resolve('/(site)/benchmark'), label: 'Benchmark' },
		{ path: '/privacy', href: resolve('/(site)/privacy'), label: 'Privacy' }
	];
</script>

<a class="skip" href="#main">Skip to content</a>
<div class="site-shell" class:landing-shell={page.url.pathname === '/'}>
<header class="site wrap">
	<a href={resolve('/(site)')} class="home" aria-label="UnScreen home"><Wordmark /></a>
	<nav aria-label="Site">
		<ul>
			{#each links as l (l.href)}
				<li><a href={l.href} aria-current={page.url.pathname === l.path ? 'page' : undefined}>{l.label}</a></li>
			{/each}
		</ul>
	</nav>
	<a class="button nav-cta" href={resolve('/(site)/app')}>Open reader <Icon name="arrow" size={16} /></a>
</header>

{@render children()}

<footer class="site-foot wrap">
	<div class="footer-brand"><a href={resolve('/(site)')} aria-label="UnScreen home"><Wordmark /></a><span>Every screen. A shared understanding.</span></div>
	<div class="footer-notes">
	<p>
		UnScreen is a student project built for the Taskforge hackathon, October 2026. Shared frames are sent to Google's
		Gemini API to be read and are not stored by UnScreen. <a href={resolve('/(site)/privacy')}>How your screen is handled</a>.
	</p>
	<p>Source publication is pending. This version is being validated locally.</p>
	</div>
</footer>
</div>

<style>
	.site {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem 2rem;
		padding-block: 1.5rem;
		min-height: 6rem;
	}
	.home {
		text-decoration: none;
	}
	nav ul {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 1.65rem;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	nav a {
		font-size: 0.85rem;
		font-weight: 400;
		color: var(--ink-soft);
		text-decoration: none;
		padding-block: 0.4rem;
		display: inline-block;
	}
	nav a:hover, nav a[aria-current='page'] {
		color: var(--ink);
		text-decoration: underline;
		text-decoration-color: var(--accent);
		text-underline-offset: 0.5em;
	}
	.site-foot {
		margin-top: 6rem;
		padding-block: 2.5rem 3rem;
		border-top: 1px solid var(--rule);
		color: var(--ink-soft);
		font-size: var(--s-1);
	}
	.site-shell {
		min-height: 100vh;
		background: radial-gradient(ellipse at 90% 0%, var(--ambient), transparent 38rem);
	}
	/* The landing is a branded scene; the reader follows the viewer's display preference. */ :global(:root:not([data-theme='light'])) .landing-shell {
		--paper: #050a16;
		--surface: #0b1425;
		--surface-raised: #101d32;
		--ink: #f1f6ff;
		--ink-soft: #acbbd1;
		--rule: #2a3a53;
		--mosaic: #3d648c;
		--accent: #93caff;
		--signal: #b9dcff;
		--on-signal: #081a30;
		--button-bg: #eef6ff;
		--button-ink: #0a1526;
		--ambient: rgb(47 112 190 / .12);
		--shadow: 0 20px 70px rgb(0 0 0 / .18);
		color-scheme: dark;
	}
	.landing-shell {
		background: var(--paper);
		color: var(--ink);
	}
	/* The landing globe rises behind the header, so the header sits above it. */
	.landing-shell .site {
		position: relative;
		z-index: 2;
	}
	.footer-brand {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		margin-bottom: 2rem;
	}
	.footer-brand a {
		text-decoration: none;
	}
	.footer-notes {
		display: flex;
		gap: 3rem;
		justify-content: space-between;
	}
	.footer-notes p:first-child {
		max-width: 70ch;
	}
	.footer-notes p:last-child {
		max-width: 29ch;
	}
	.nav-cta {
		font-size: 0.8rem;
		min-height: 2.4rem;
	}
	@media (max-width: 960px) {
		.site {
			flex-wrap: wrap;
			gap: 1.1rem;
		}
		nav {
			order: 3;
			width: 100%;
		}
		nav ul {
			justify-content: space-between;
			gap: 0.5rem 1rem;
		}
		.footer-notes {
			display: block;
		}
		.footer-notes p:last-child {
			max-width: var(--measure);
		}
	}
	@media (max-width: 520px) {
		.footer-brand {
			align-items: start;
			flex-direction: column;
		}
		nav a {
			font-size: 0.78rem;
		}
	}
	@media (max-width: 420px) {
		.site {
			gap: 1rem .5rem;
		}
		.nav-cta {
			font-size: .7rem;
			min-height: 2.2rem;
			padding: .5em .85em;
		}
		nav ul {
			gap: .35rem .45rem;
		}
		nav a {
			font-size: .68rem;
		}
	}
</style>
