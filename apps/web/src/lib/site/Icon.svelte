<script lang="ts">
	let { name, size = 20 }: { name: 'screen' | 'arrow' | 'play' | 'table' | 'code' | 'text' | 'check' | 'shield' | 'spark' | 'sound' | 'pointer' | 'history' | 'settings'; size?: number } = $props();
</script>

<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
	{#if name === 'screen'}<rect x="3" y="4" width="18" height="13" rx="3" /><path d="M8 21h8m-4-4v4M8 8h8M8 12h5" />
	{:else if name === 'arrow'}<path d="M5 12h14m-6-6 6 6-6 6" />
	{:else if name === 'play'}<path d="m9 5 11 7-11 7z" />
	{:else if name === 'table'}<rect x="3" y="4" width="18" height="16" rx="3" /><path d="M3 10h18M3 15h18M10 4v16" />
	{:else if name === 'code'}<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18" />
	{:else if name === 'text'}<path d="M4 5h16M12 5v15M8 20h8M4 9V5m16 4V5" />
	{:else if name === 'check'}<path d="m5 12 4 4L19 6" />
	{:else if name === 'shield'}<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6z" /><path d="m8 12 3 3 5-6" />
	{:else if name === 'spark'}<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z" />
	{:else if name === 'sound'}<path d="m11 4-6 5H2v6h3l6 5zm5 4a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14" />
	{:else if name === 'pointer'}<path d="m5 3 15 9-7 2-3 7z" />
	{:else if name === 'history'}<path d="M3 11a9 9 0 1 1 2 7M3 5v6h6m3-5v6l4 2" />
	{:else}<path d="M4 7h16M4 17h16" /><circle cx="9" cy="7" r="3" fill="var(--surface)" /><circle cx="15" cy="17" r="3" fill="var(--surface)" />{/if}
</svg>
