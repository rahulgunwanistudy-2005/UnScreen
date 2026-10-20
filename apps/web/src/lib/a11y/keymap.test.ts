import { describe, expect, it } from 'vitest';
import { conflict, DEFAULT_KEYMAP, describe as describeChord, fromEvent, match, parseKeymap } from './keymap.ts';

const ev = (code: string, key: string, mods: Partial<Record<'altKey' | 'shiftKey' | 'ctrlKey' | 'metaKey', boolean>> = {}) => ({
	code,
	key,
	altKey: false,
	shiftKey: false,
	ctrlKey: false,
	metaKey: false,
	...mods
});

describe('keymap', () => {
	it('matches Alt+Shift chords by physical key, even when macOS composes a character', () => {
		expect(match(DEFAULT_KEYMAP, fromEvent(ev('KeyS', 'Í', { altKey: true, shiftKey: true })))).toBe('toggleCapture');
		expect(match(DEFAULT_KEYMAP, fromEvent(ev('KeyS', 's')))).toBeNull();
	});

	it('defaults have no duplicates and no reserved chords', () => {
		for (const [action, chord] of Object.entries(DEFAULT_KEYMAP)) {
			expect(conflict(DEFAULT_KEYMAP, action as keyof typeof DEFAULT_KEYMAP, chord!)).toBeNull();
		}
	});

	it('refuses bare keys, NVDA table navigation and duplicates', () => {
		expect(conflict(DEFAULT_KEYMAP, 'openHelp', fromEvent(ev('KeyT', 't')))?.reason).toBe('bare');
		expect(
			conflict(DEFAULT_KEYMAP, 'openHelp', fromEvent(ev('ArrowLeft', 'ArrowLeft', { ctrlKey: true, altKey: true })))?.reason
		).toBe('reserved');
		const dup = conflict(DEFAULT_KEYMAP, 'openHelp', DEFAULT_KEYMAP.toggleCapture!);
		expect(dup).toEqual({ reason: 'duplicate', with: 'toggleCapture' });
	});

	it('describes and parses stored maps, including turned-off actions', () => {
		expect(describeChord(DEFAULT_KEYMAP.whereIsPointer)).toBe('Alt+Shift+P');
		expect(describeChord(null)).toBe('Off');
		const parsed = parseKeymap({ repeatLast: null, readSummary: { key: 'q', alt: true, ctrl: true }, junk: 1 });
		expect(parsed.repeatLast).toBeNull();
		expect(parsed.readSummary).toEqual({ key: 'q', alt: true, shift: false, ctrl: true, meta: false });
		expect(parseKeymap('nonsense')).toEqual(DEFAULT_KEYMAP);
	});
});
