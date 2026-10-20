import { createRng } from './rng.ts';

export type SlideBlock = { kind: 'heading' | 'paragraph' | 'list_item'; level: number | null; text: string };

export type SlideFixture = {
	seed: number;
	kind: 'slide' | 'doc';
	title: string;
	blocks: SlideBlock[];
	theme: 'light' | 'dark' | 'accent';
};

const DECKS = [
	{
		title: 'Sprint 42 review',
		points: [
			'Shipped CSV export to all workspaces',
			'Login timeout fixed for SSO users',
			'Search latency down from 840 ms to 310 ms',
			'Two incidents, both resolved within an hour',
			'Next sprint: billing alerts and bulk invite'
		]
	},
	{
		title: 'Lecture 7: Virtual memory',
		points: [
			'Each process sees its own address space',
			'Pages are 4 KiB on most x86 systems',
			'The TLB caches recent translations',
			'A page fault traps into the kernel',
			'Thrashing happens when the working set exceeds RAM'
		]
	},
	{
		title: 'Q3 results',
		points: [
			'Revenue grew 18% quarter on quarter',
			'Churn fell to 2.1% from 2.9%',
			'Three new enterprise accounts signed',
			'Hiring paused until January',
			'Cash runway: 22 months'
		]
	},
	{
		title: 'Lab safety briefing',
		points: [
			'Goggles on before entering bay 3',
			'Report every spill, however small',
			'Fume hood sash stays below the line',
			'No food or drink past the yellow tape',
			'Emergency shower is next to door B'
		]
	},
	{
		title: 'Onboarding checklist',
		points: [
			'Set up two-factor authentication',
			'Join the team channel and standup',
			'Read the architecture overview',
			'Pair with your buddy on a first ticket',
			'Book a 30-minute check-in for week two'
		]
	}
] as const;

const DOC_PARAS = [
	'This document describes how the service handles retries when a downstream dependency fails.',
	'Requests are retried up to three times with exponential backoff starting at 200 milliseconds.',
	'Idempotency keys make retries safe for payment and invite endpoints.',
	'Alerts fire when the retry rate exceeds 5% over a ten-minute window.',
	'Owners review the dashboard every Monday and file tickets for regressions.'
] as const;

export function generateSlide(seed: number): SlideFixture {
	const rng = createRng(seed);
	const deck = DECKS[seed % DECKS.length];
	const asDoc = seed % 2 === 1;
	const count = rng.int(3, deck.points.length);
	if (asDoc) {
		const paras = rng.shuffle(DOC_PARAS).slice(0, rng.int(2, 4));
		return {
			seed,
			kind: 'doc',
			title: deck.title,
			blocks: [
				{ kind: 'heading', level: 1, text: deck.title },
				{ kind: 'paragraph', level: null, text: paras[0] },
				{ kind: 'heading', level: 2, text: 'Key points' },
				...deck.points.slice(0, count).map((text) => ({ kind: 'list_item' as const, level: null, text })),
				{ kind: 'heading', level: 2, text: 'Details' },
				...paras.slice(1).map((text) => ({ kind: 'paragraph' as const, level: null, text }))
			],
			theme: 'light'
		};
	}
	return {
		seed,
		kind: 'slide',
		title: deck.title,
		blocks: [
			{ kind: 'heading', level: 1, text: deck.title },
			...deck.points.slice(0, count).map((text) => ({ kind: 'list_item' as const, level: null, text }))
		],
		theme: rng.pick(['light', 'dark', 'accent'] as const)
	};
}
