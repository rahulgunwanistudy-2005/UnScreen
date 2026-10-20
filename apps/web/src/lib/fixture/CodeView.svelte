<script lang="ts">
	import type { CodeFixture } from './code.ts';

	let { code, firstLine = 0, maxLines = 40 }: { code: CodeFixture; firstLine?: number; maxLines?: number } =
		$props();

	const visible = $derived(code.lines.slice(firstLine, firstLine + maxLines));
	const KEYWORDS =
		/\b(import|from|def|class|return|if|else|for|in|const|let|function|export|package|func|var|type|struct|select|case|typedef|int|void|double|while|async|await|new|true|false|None|True|False|nil)\b/g;
	type Tok = { t: string; k: 'kw' | 'str' | 'num' | 'com' | 'txt' };

	function tokens(line: string): Tok[] {
		const comment = line.search(/(#|\/\/)(?![^'"]*['"][^'"]*$)/);
		const body = comment >= 0 ? line.slice(0, comment) : line;
		const out: Tok[] = [];
		const re = /("[^"]*"|'[^']*'|`[^`]*`|\b\d+(?:\.\d+)?\b)/g;
		let last = 0;
		for (const m of body.matchAll(re)) {
			const idx = m.index ?? 0;
			if (idx > last) out.push(...words(body.slice(last, idx)));
			out.push({ t: m[0], k: /^\d/.test(m[0]) ? 'num' : 'str' });
			last = idx + m[0].length;
		}
		if (last < body.length) out.push(...words(body.slice(last)));
		if (comment >= 0) out.push({ t: line.slice(comment), k: 'com' });
		return out;
	}
	function words(s: string): Tok[] {
		const out: Tok[] = [];
		let last = 0;
		for (const m of s.matchAll(KEYWORDS)) {
			const idx = m.index ?? 0;
			if (idx > last) out.push({ t: s.slice(last, idx), k: 'txt' });
			out.push({ t: m[0], k: 'kw' });
			last = idx + m[0].length;
		}
		if (last < s.length) out.push({ t: s.slice(last), k: 'txt' });
		return out;
	}
</script>

<div class="ide" class:light={code.theme === 'light'} style:--size="{code.fontPx}px">
	<div class="activity" aria-hidden="true"></div>
	<div class="main">
		<div class="tabs">
			<span class="tab active">{code.fileName}</span>
			<span class="tab">README.md</span>
		</div>
		<div class="crumbs">src &gt; {code.fileName}</div>
		<div class="editor">
			{#each visible as line, i (i)}
				<div class="line" class:current={code.cursor.line === firstLine + i}>
					<span class="gutter">{firstLine + i + 1}</span>
					<span class="text" data-truth="l{firstLine + i + 1}"
						>{#each tokens(line) as tok, j (j)}<span class={tok.k}>{tok.t}</span>{/each}{#if code.cursor.line === firstLine + i}<span
								class="caret"
							></span>{/if}</span
					>
				</div>
			{/each}
		</div>
		<div class="status">
			<span>Ln {code.cursor.line + 1}, Col {code.cursor.col + 1}</span>
			<span>{code.language}</span>
			<span>UTF-8</span>
		</div>
	</div>
</div>

<style>
	.ide {
		--bg: #1e1e1e;
		--fg: #d4d4d4;
		--gutter: #858585;
		--chrome: #252526;
		--tab: #2d2d2d;
		--kw: #569cd6;
		--str: #ce9178;
		--num: #b5cea8;
		--com: #6a9955;
		--cur: #2a2d2e;
		width: 100%;
		height: 100%;
		display: flex;
		background: var(--bg);
		color: var(--fg);
	}
	.light {
		--bg: #ffffff;
		--fg: #1f1f1f;
		--gutter: #6e7681;
		--chrome: #f3f3f3;
		--tab: #ececec;
		--kw: #0000ff;
		--str: #a31515;
		--num: #098658;
		--com: #008000;
		--cur: #f0f0f0;
	}
	.activity {
		width: 48px;
		background: var(--chrome);
	}
	.main {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}
	.tabs {
		display: flex;
		background: var(--chrome);
		font: 13px system-ui, sans-serif;
	}
	.tab {
		padding: 8px 16px;
		opacity: 0.7;
	}
	.tab.active {
		background: var(--bg);
		opacity: 1;
	}
	.crumbs {
		padding: 4px 16px;
		font: 12px system-ui, sans-serif;
		opacity: 0.7;
	}
	.editor {
		flex: 1;
		overflow: hidden;
		font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace;
		font-size: var(--size);
		line-height: 1.5;
	}
	.line {
		display: flex;
		white-space: pre;
	}
	.current {
		background: var(--cur);
	}
	.gutter {
		width: 56px;
		padding-right: 16px;
		text-align: right;
		color: var(--gutter);
		flex: none;
	}
	.kw {
		color: var(--kw);
	}
	.str {
		color: var(--str);
	}
	.num {
		color: var(--num);
	}
	.com {
		color: var(--com);
		font-style: italic;
	}
	.caret {
		display: inline-block;
		width: 2px;
		height: 1.2em;
		vertical-align: text-bottom;
		background: var(--fg);
	}
	.status {
		display: flex;
		gap: 24px;
		padding: 3px 16px;
		background: #007acc;
		color: #fff;
		font: 12px system-ui, sans-serif;
	}
</style>
