import type { Announce } from '@unscreen/schema';
import { describe, expect, it } from 'vitest';
import { Announcer, passes } from './announcer.ts';

function fakeClock() {
	let t = 0;
	let timers: { at: number; fn: () => void; id: number }[] = [];
	let next = 0;
	return {
		now: () => t,
		setTimeout: (fn: () => void, ms: number) => {
			timers.push({ at: t + ms, fn, id: ++next });
			return next;
		},
		clearTimeout: (id: unknown) => {
			timers = timers.filter((x) => x.id !== id);
		},
		advance(ms: number) {
			const end = t + ms;
			for (;;) {
				timers.sort((a, b) => a.at - b.at);
				const due = timers[0];
				if (!due || due.at > end) break;
				timers.shift();
				t = due.at;
				due.fn();
			}
			t = end;
		}
	};
}

const a = (text: string, extra: Partial<Announce> = {}): Announce => ({
	type: 'announce',
	version: 2,
	priority: 'other',
	kind: 'cell',
	text,
	refs: [],
	...extra
});

describe('Announcer', () => {
	it('coalesces a burst into one utterance after the window', () => {
		const clock = fakeClock();
		const said: string[] = [];
		const ann = new Announcer((s) => said.push(s), undefined, clock);
		ann.push(a('One.'));
		clock.advance(500);
		ann.push(a('Two.'));
		clock.advance(999);
		expect(said).toEqual([]);
		clock.advance(1);
		expect(said).toEqual(['One. Two.']);
	});

	it('throttles to one utterance per 2 seconds', () => {
		const clock = fakeClock();
		const said: string[] = [];
		const ann = new Announcer((s) => said.push(s), undefined, clock);
		ann.push(a('One.'));
		clock.advance(1500);
		ann.push(a('Two.'));
		clock.advance(1500);
		expect(said).toEqual(['One.']);
		clock.advance(500);
		expect(said).toEqual(['One.', 'Two.']);
	});

	it('orders by priority and summarises overflow', () => {
		const clock = fakeClock();
		const said: string[] = [];
		const ann = new Announcer((s) => said.push(s), { coalesceMs: 100, minGapMs: 0, maxItems: 2 }, clock);
		ann.push(a('Other 1.'));
		ann.push(a('Other 2.'));
		ann.push(a('Focus.', { priority: 'focus' }));
		ann.push(a('Other 3.'));
		clock.advance(100);
		expect(said).toEqual(['Focus. Other 1. 2 more changes in the Changes list.']);
	});

	it('drops what came before a content switch in the same burst', () => {
		const clock = fakeClock();
		const said: string[] = [];
		const ann = new Announcer((s) => said.push(s), { coalesceMs: 100, minGapMs: 0, maxItems: 4 }, clock);
		ann.push(a('Old cell.', { version: 3 }));
		ann.push(a('Now showing: Code.', { version: 4, kind: 'content_type', priority: 'content_type' }));
		clock.advance(100);
		expect(said).toEqual(['Now showing: Code.']);
	});

	it('verbosity filters by kind but never drops focus or content switches', () => {
		expect(passes({ priority: 'other', kind: 'cell' }, 'important')).toBe(false);
		expect(passes({ priority: 'other', kind: 'row_added' }, 'important')).toBe(true);
		expect(passes({ priority: 'other', kind: 'row_added' }, 'quiet')).toBe(false);
		expect(passes({ priority: 'focus', kind: 'cell' }, 'quiet')).toBe(true);
		expect(passes({ priority: 'content_type', kind: 'content_type' }, 'quiet')).toBe(true);
	});
});
