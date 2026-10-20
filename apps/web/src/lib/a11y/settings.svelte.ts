import { DEFAULT_KEYMAP, parseKeymap, type Keymap } from './keymap.ts';
import type { Verbosity } from './announcer.ts';

export type Preferences = {
	verbosity: Verbosity;
	numericStyle: 'old_to_new' | 'new_only';
	largePrint: boolean;
	motion: 'system' | 'reduce';
	theme: 'system' | 'light' | 'dark';
	shortcuts: boolean;
	keymap: Keymap;
};

const KEY = 'unscreen:prefs:v1';

export const DEFAULT_PREFS: Preferences = {
	verbosity: 'all',
	numericStyle: 'old_to_new',
	largePrint: false,
	motion: 'system',
	theme: 'system',
	shortcuts: true,
	keymap: DEFAULT_KEYMAP
};

function load(): Preferences {
	try {
		const raw = JSON.parse(localStorage.getItem(KEY) ?? 'null') as Partial<Preferences> | null;
		if (!raw || typeof raw !== 'object') return { ...DEFAULT_PREFS };
		return {
			verbosity: ['all', 'important', 'quiet'].includes(raw.verbosity as string) ? raw.verbosity! : 'all',
			numericStyle: raw.numericStyle === 'new_only' ? 'new_only' : 'old_to_new',
			largePrint: raw.largePrint === true,
			motion: raw.motion === 'reduce' ? 'reduce' : 'system',
			theme: raw.theme === 'light' || raw.theme === 'dark' ? raw.theme : 'system',
			shortcuts: raw.shortcuts !== false,
			keymap: parseKeymap(raw.keymap)
		};
	} catch {
		return { ...DEFAULT_PREFS };
	}
}

/** Per-viewer preferences, kept in this browser only. */
class PrefsStore {
	value = $state<Preferences>({ ...DEFAULT_PREFS });
	private loaded = false;

	init(): void {
		if (this.loaded || typeof localStorage === 'undefined') return;
		this.loaded = true;
		this.value = load();
		this.apply();
	}

	update(patch: Partial<Preferences>): void {
		this.value = { ...this.value, ...patch };
		try {
			localStorage.setItem(KEY, JSON.stringify(this.value));
		} catch {
			// Private mode or storage blocked: preferences last for this visit only.
		}
		this.apply();
	}

	private apply(): void {
		if (typeof document === 'undefined') return;
		const root = document.documentElement;
		if (this.value.theme === 'system') delete root.dataset.theme;
		else root.dataset.theme = this.value.theme;
		root.dataset.largePrint = String(this.value.largePrint);
		root.dataset.motion = this.value.motion;
	}
}

export const prefs = new PrefsStore();
