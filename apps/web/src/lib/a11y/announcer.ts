import type { Announce } from '@unscreen/schema';

export type Verbosity = 'all' | 'important' | 'quiet';

export type AnnouncerConfig = {
	/** Changes arriving within this window are spoken together. */
	coalesceMs: number;
	/** Never speak more often than this. */
	minGapMs: number;
	/** Longest single utterance; the rest is summarised. */
	maxItems: number;
};

export const DEFAULT_ANNOUNCER: AnnouncerConfig = { coalesceMs: 1500, minGapMs: 2000, maxItems: 4 };

type Clock = { now(): number; setTimeout(fn: () => void, ms: number): unknown; clearTimeout(id: unknown): void };

const realClock: Clock = {
	now: () => Date.now(),
	setTimeout: (fn, ms) => setTimeout(fn, ms),
	clearTimeout: (id) => clearTimeout(id as ReturnType<typeof setTimeout>)
};

const IMPORTANT_KINDS = new Set<Announce['kind']>([
	'content_type',
	'title',
	'row_added',
	'row_removed',
	'lines_added',
	'lines_removed',
	'scroll',
	'status'
]);

export function passes(a: Pick<Announce, 'priority' | 'kind'>, verbosity: Verbosity): boolean {
	if (a.priority === 'content_type' || a.priority === 'focus') return true;
	if (verbosity === 'all') return true;
	if (verbosity === 'important') return IMPORTANT_KINDS.has(a.kind);
	return false;
}

const RANK: Record<Announce['priority'], number> = { content_type: 0, focus: 1, other: 2 };

/**
 * One polite live region, fed through a queue that coalesces bursts and throttles speech so
 * the reader is not interrupted mid-row by every keystroke the presenter makes.
 */
export class Announcer {
	private queue: Announce[] = [];
	private timer: unknown = null;
	private lastSpoke = -Infinity;
	verbosity: Verbosity = 'all';

	constructor(
		private speak: (text: string) => void,
		private config: AnnouncerConfig = DEFAULT_ANNOUNCER,
		private clock: Clock = realClock
	) {}

	push(a: Announce): void {
		if (!passes(a, this.verbosity)) return;
		this.queue.push(a);
		if (this.timer === null) this.schedule(this.config.coalesceMs);
	}

	/** Speak immediately, outside the queue (used for direct answers to the user's own keys). */
	now(text: string): void {
		this.speak(text);
		this.lastSpoke = this.clock.now();
	}

	clear(): void {
		this.queue = [];
		if (this.timer !== null) this.clock.clearTimeout(this.timer);
		this.timer = null;
	}

	private schedule(ms: number): void {
		this.timer = this.clock.setTimeout(() => this.flush(), ms);
	}

	private flush(): void {
		this.timer = null;
		if (this.queue.length === 0) return;
		const wait = this.lastSpoke + this.config.minGapMs - this.clock.now();
		if (wait > 0) {
			this.schedule(wait);
			return;
		}
		const items = [...this.queue].sort((a, b) => RANK[a.priority] - RANK[b.priority]);
		this.queue = [];
		const switched = items.findLastIndex((a) => a.kind === 'content_type');
		const relevant = switched >= 0 ? items.filter((a, i) => i === switched || a.version > items[switched].version) : items;
		const spoken = relevant.slice(0, this.config.maxItems).map((a) => a.text);
		const rest = relevant.length - spoken.length;
		if (rest > 0) spoken.push(`${rest} more ${rest === 1 ? 'change' : 'changes'} in the Changes list.`);
		this.speak(spoken.join(' '));
		this.lastSpoke = this.clock.now();
	}
}
