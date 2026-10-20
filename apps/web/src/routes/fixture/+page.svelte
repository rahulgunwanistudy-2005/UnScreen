<svelte:head><title>Test fixtures | UnScreen</title></svelte:head>

<main class="list">
	<h1>Test fixtures</h1>
	<p>
		These pages are scripted test fixtures, not real meeting content. They edit themselves on a timer
		so UnScreen can be tested and demonstrated without a live presenter.
	</p>
	<ul>
		<li><a href="/fixture/sheet?seed=1">Spreadsheet that changes every 8 seconds</a></li>
		<li><a href="/fixture/sheet?seed=1&frame=meet">The same spreadsheet inside a meeting window</a></li>
		<li><a href="/fixture/code?seed=1">Code editor that changes every 8 seconds</a></li>
		<li><a href="/fixture/slide?seed=2">Slide</a></li>
		<li><a href="/fixture/slide?seed=3">Document</a></li>
	</ul>
</main>

<style>
	.list {
		max-width: 40rem;
		margin: 2rem auto;
		padding: 0 1rem;
		font: 1.1rem/1.6 system-ui, sans-serif;
		overflow: auto;
	}
</style>
