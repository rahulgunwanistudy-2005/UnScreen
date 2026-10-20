import type { Document, Patch, Snapshot } from '@unscreen/schema';
import { applyPatch, PatchError } from './patch.ts';

export type HistoryEntry = {
	version: number;
	at: number;
	summary: string;
	doc: Document;
};

const HISTORY_LIMIT = 200;

/** The live document plus a rewindable history of versions. */
export class DocStore {
	doc = $state<Document | null>(null);
	history = $state<HistoryEntry[]>([]);

	get version(): number {
		return this.doc?.version ?? 0;
	}

	snapshot(msg: Snapshot): void {
		this.doc = msg.doc;
		this.record('Started reading');
	}

	/** Returns false when the patch does not fit our version; the caller must resync. */
	patch(msg: Patch): boolean {
		if (!this.doc || msg.base !== this.doc.version) return false;
		try {
			applyPatch(this.doc as unknown as Record<string, unknown>, msg.ops);
		} catch (err) {
			if (err instanceof PatchError) return false;
			throw err;
		}
		this.doc.version = msg.version;
		return true;
	}

	/** Called after the announcements for a version arrive, so history carries their text. */
	record(summary: string): void {
		if (!this.doc) return;
		const entry = { version: this.doc.version, at: Date.now(), summary, doc: $state.snapshot(this.doc) as Document };
		const last = this.history[0];
		if (last && last.version === entry.version) {
			last.summary = last.summary === 'Started reading' ? summary : `${last.summary} ${summary}`;
			last.doc = entry.doc;
			return;
		}
		this.history = [entry, ...this.history].slice(0, HISTORY_LIMIT);
	}

	clear(): void {
		this.doc = null;
		this.history = [];
	}
}
