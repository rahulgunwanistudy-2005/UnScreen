/**
 * Keyboard shortcuts. Defaults are Alt+Shift chords: NVDA uses Insert/CapsLock as its
 * modifier and Ctrl+Alt+arrows for table navigation, browsers use Ctrl/Cmd chords, and
 * single letters belong to browse-mode quick navigation. Alt+Shift+letter collides with none
 * of these on Windows or macOS (VoiceOver uses Ctrl+Option).
 */

export type Action =
	| 'toggleCapture'
	| 'readSummary'
	| 'whereIsPointer'
	| 'focusAsk'
	| 'focusContent'
	| 'focusChanges'
	| 'repeatLast'
	| 'cycleVerbosity'
	| 'openHelp';

export type Chord = { key: string; alt: boolean; shift: boolean; ctrl: boolean; meta: boolean };

export type Keymap = Record<Action, Chord | null>;

export const ACTION_LABELS: Record<Action, string> = {
	toggleCapture: 'Start or stop reading the shared screen',
	readSummary: 'Say what is being shared',
	whereIsPointer: "Say what the presenter's pointer is on",
	focusAsk: 'Ask a question about the screen',
	focusContent: 'Jump to the shared content',
	focusChanges: 'Jump to the list of changes',
	repeatLast: 'Repeat the last announcement',
	cycleVerbosity: 'Change how much is announced',
	openHelp: 'Open keyboard help'
};

const chord = (key: string): Chord => ({ key, alt: true, shift: true, ctrl: false, meta: false });

export const DEFAULT_KEYMAP: Keymap = {
	toggleCapture: chord('s'),
	readSummary: chord('w'),
	whereIsPointer: chord('p'),
	focusAsk: chord('a'),
	focusContent: chord('c'),
	focusChanges: chord('h'),
	repeatLast: chord('r'),
	cycleVerbosity: chord('v'),
	openHelp: chord('k')
};

/** Chords that screen readers or browsers already own. */
const RESERVED: Chord[] = [
	{ key: 'arrowleft', alt: true, shift: false, ctrl: true, meta: false },
	{ key: 'arrowright', alt: true, shift: false, ctrl: true, meta: false },
	{ key: 'arrowup', alt: true, shift: false, ctrl: true, meta: false },
	{ key: 'arrowdown', alt: true, shift: false, ctrl: true, meta: false },
	{ key: 'tab', alt: false, shift: false, ctrl: false, meta: false },
	{ key: 'tab', alt: false, shift: true, ctrl: false, meta: false },
	{ key: 'f5', alt: false, shift: false, ctrl: false, meta: false },
	{ key: 'l', alt: false, shift: false, ctrl: true, meta: false },
	{ key: 'w', alt: false, shift: false, ctrl: true, meta: false },
	{ key: 't', alt: false, shift: false, ctrl: true, meta: false },
	{ key: 'f4', alt: true, shift: false, ctrl: false, meta: false }
];

/**
 * `event.key` with Alt held on macOS gives a composed character (Alt+Shift+S is "Í"), so match
 * on `event.code` for letters and digits.
 */
export function eventKey(e: Pick<KeyboardEvent, 'key' | 'code'>): string {
	if (/^Key[A-Z]$/.test(e.code)) return e.code.slice(3).toLowerCase();
	if (/^Digit[0-9]$/.test(e.code)) return e.code.slice(5);
	return e.key.toLowerCase();
}

export function fromEvent(e: Pick<KeyboardEvent, 'key' | 'code' | 'altKey' | 'shiftKey' | 'ctrlKey' | 'metaKey'>): Chord {
	return { key: eventKey(e), alt: e.altKey, shift: e.shiftKey, ctrl: e.ctrlKey, meta: e.metaKey };
}

export function same(a: Chord, b: Chord): boolean {
	return a.key === b.key && a.alt === b.alt && a.shift === b.shift && a.ctrl === b.ctrl && a.meta === b.meta;
}

export function match(map: Keymap, c: Chord): Action | null {
	for (const [action, bound] of Object.entries(map) as [Action, Chord | null][]) {
		if (bound && same(bound, c)) return action;
	}
	return null;
}

export type Conflict = { reason: 'reserved' | 'duplicate' | 'bare'; with?: Action };

/** Why a chord cannot be bound to `action`, or null if it can. */
export function conflict(map: Keymap, action: Action, c: Chord): Conflict | null {
	if (!c.alt && !c.ctrl && !c.meta) return { reason: 'bare' };
	if (RESERVED.some((r) => same(r, c))) return { reason: 'reserved' };
	const other = match(map, c);
	if (other && other !== action) return { reason: 'duplicate', with: other };
	return null;
}

export function describe(c: Chord | null): string {
	if (!c) return 'Off';
	const parts: string[] = [];
	if (c.ctrl) parts.push('Ctrl');
	if (c.meta) parts.push('Cmd');
	if (c.alt) parts.push('Alt');
	if (c.shift) parts.push('Shift');
	const key = c.key.length === 1 ? c.key.toUpperCase() : c.key.charAt(0).toUpperCase() + c.key.slice(1);
	parts.push(key);
	return parts.join('+');
}

export function parseKeymap(raw: unknown): Keymap {
	const map: Keymap = { ...DEFAULT_KEYMAP };
	if (!raw || typeof raw !== 'object') return map;
	for (const action of Object.keys(DEFAULT_KEYMAP) as Action[]) {
		const v = (raw as Record<string, unknown>)[action];
		if (v === null) map[action] = null;
		else if (v && typeof v === 'object' && typeof (v as Chord).key === 'string') {
			const c = v as Chord;
			map[action] = { key: c.key, alt: !!c.alt, shift: !!c.shift, ctrl: !!c.ctrl, meta: !!c.meta };
		}
	}
	return map;
}
