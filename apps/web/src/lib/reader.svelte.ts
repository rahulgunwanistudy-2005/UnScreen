import type { Announce } from '@unscreen/schema';
import { Announcer } from './a11y/announcer.ts';
import { SpeechPreview } from './a11y/speech.ts';
import { prefs } from './a11y/settings.svelte.ts';
import { CaptureError, ScreenCapture } from './capture/capture.ts';
import { DocStore } from './doc/store.svelte.ts';
import { EngineClient, type ConnectionState, type ServerMessage } from './engine/client.ts';
import type { RecordedSession } from './recording/types.ts';

export type Phase = 'idle' | 'starting' | 'reading' | 'recording' | 'stopped';

export type AnswerEntry = { q: string; text: string; refs: string[]; version: number };

const POINTER_SEND_MS = 500;

/** Wires capture, engine, document and speech together for the reader page. */
export class ReaderSession {
	phase = $state<Phase>('idle');
	connection = $state<ConnectionState>('idle');
	status = $state('Not reading. Press Start, then choose the meeting tab or window.');
	alert = $state('');
	live = $state('');
	busy = $state(false);
	pointerText = $state<string | null>(null);
	pointerRef = $state<string | null>(null);
	answers = $state<AnswerEntry[]>([]);
	lastLatencyMs = $state<number | null>(null);
	workerCpuMs = $state(0);
	changed = $state<Record<string, number>>({});
	readonly doc = new DocStore();
	recordingSource = $state<string | null>(null);
	private playbackTimers: ReturnType<typeof setTimeout>[] = [];
	private speech = new SpeechPreview();

	setHearIt(enabled: boolean): void {
		this.speech.setEnabled(enabled);
	}

	private lastSpoken = '';
	private announcer = new Announcer((text) => this.say(text));
	private engine: EngineClient;
	private capture: ScreenCapture;
	private pointer: { x: number; y: number } | null = null;
	private pointerSentAt = 0;
	private pointerAsked = false;
	private frameSentAt: Record<number, number> = {};
	private focusRef: string | null = null;

	constructor() {
		this.engine = new EngineClient({
			message: (m) => this.onMessage(m),
			state: (s, detail) => this.onConnection(s, detail),
			fresh: () => this.capture.resend(),
			resumeVersion: () => (this.doc.doc ? this.doc.version : null)
		});
		this.capture = new ScreenCapture({
			frame: (f) => {
				// Content and cursor motion may overlap; a previously tracked point
				// cannot be treated as current until the tracker sees another clean move.
				this.pointer = null;
				this.pointerText = null;
				this.pointerRef = null;
				this.frameSentAt[this.doc.version] = performance.now();
				this.engine.sendFrame({
					meta: { w: f.w, h: f.h, mime: 'image/webp', change_score: f.score, changed_tiles: f.tiles, pointer: null },
					data: f.blob
				});
			},
			pointer: (x, y) => this.onPointer(x, y),
			ended: () => this.onShareEnded(),
			cpu: (ms) => (this.workerCpuMs = this.workerCpuMs * 0.9 + ms * 0.1)
		});
	}

	/** Polite live region. Re-speaking identical text needs the content to change, so toggle a no-break space. */
	private say(text: string): void {
		this.lastSpoken = text;
		this.speech.say(text);
		this.live = this.live === text ? `${text}\u00a0` : text;
	}

	private shout(text: string): void {
		this.alert = '';
		this.speech.say(text);
		queueMicrotask(() => (this.alert = text));
	}

	get verbosity() {
		return prefs.value.verbosity;
	}

	async start(): Promise<void> {
		if (this.phase === 'starting' || this.phase === 'reading') return;
		this.phase = 'starting';
		this.alert = '';
		this.recordingSource = null;
		this.status = 'Choose the meeting tab or window to read.';
		this.announcer.verbosity = prefs.value.verbosity;
		try {
			await this.capture.start();
		} catch (err) {
			this.phase = 'idle';
			const message = err instanceof CaptureError ? err.message : 'Could not start screen capture.';
			this.status = message;
			this.shout(message);
			return;
		}
		this.resetContent();
		this.phase = 'reading';
		this.status = 'Reading the shared screen. Waiting for the first picture.';
		this.announcer.now('Started. Reading the shared screen.');
		await this.engine.start();
		this.pushSettings();
	}

	stop(spoken = 'Stopped reading. The last version stays on the page.'): void {
		for (const timer of this.playbackTimers) clearTimeout(timer);
		this.playbackTimers = [];
		this.speech.stop();
		if (this.phase !== 'reading' && this.phase !== 'starting' && this.phase !== 'recording') return;
		this.capture.stop();
		this.engine.stop();
		this.announcer.clear();
		this.phase = 'stopped';
		this.status = spoken;
		this.announcer.now(spoken);
		this.speech.stop();
	}

	toggle(): void {
		if (this.phase === 'recording') this.stop('Recording stopped. The last recorded version stays on the page.');
		else if (this.phase === 'reading' || this.phase === 'starting') this.stop();
		else void this.start();
	}

	private resetContent(): void {
		this.doc.clear();
		this.changed = {};
		this.answers = [];
		this.pointer = null;
		this.pointerText = null;
		this.pointerRef = null;
		this.pointerAsked = false;
		this.pointerSentAt = 0;
		this.focusRef = null;
		this.frameSentAt = {};
		this.lastLatencyMs = null;
		this.busy = false;
	}

	playRecording(recording: RecordedSession): void {
		this.stop();
		this.resetContent();
		this.alert = '';
		this.phase = 'recording';
		this.recordingSource = recording.source;
		this.status = 'Playing a recorded session at twice its original speed.';
		this.announcer.now('Playing a recorded session at twice its original speed.');
		for (const event of recording.events) {
			this.playbackTimers.push(setTimeout(() => {
				if (this.phase === 'recording') this.onMessage(structuredClone(event.message));
			}, event.at / recording.playback_rate));
		}
		const end = recording.events[recording.events.length - 1].at / recording.playback_rate + 2500;
		this.playbackTimers.push(setTimeout(() => {
			this.phase = 'stopped';
			this.busy = false;
			this.status = 'Recording complete. The last recorded version stays on the page.';
			this.playbackTimers = [];
		}, end));
	}

	setFocus(ref: string | null): void {
		if (ref === this.focusRef) return;
		this.focusRef = ref;
		this.pushSettings();
	}

	pushSettings(): void {
		this.announcer.verbosity = prefs.value.verbosity;
		this.engine.send({
			type: 'settings',
			verbosity: prefs.value.verbosity,
			numeric_style: prefs.value.numericStyle,
			focus_ref: this.focusRef
		});
	}

	ask(q: string): boolean {
		const question = q.trim();
		if (!question) return false;
		const sent = this.engine.send({ type: 'ask', q: question, version: this.doc.version });
		if (!sent) {
			this.announcer.now('Start reading the shared screen before asking about it.');
			return false;
		}
		this.announcer.now('Asking.');
		return true;
	}

	whereIsPointer(): void {
		if (!this.pointer) {
			this.announcer.now(
				this.phase === 'reading' ? "No pointer movement seen yet. Ask again after the presenter moves the mouse." : 'Not reading yet.'
			);
			return;
		}
		this.pointerAsked = true;
		if (!this.engine.send({ type: 'pointer', xy: this.pointer })) {
			this.pointerAsked = false;
			this.announcer.now(this.pointerText ?? 'Not connected to the reading engine.');
		}
	}

	readSummary(): void {
		const d = this.doc.doc;
		if (!d) {
			this.announcer.now(this.phase === 'reading' ? 'Nothing read yet. Waiting for the first picture.' : 'Not reading.');
			return;
		}
		this.announcer.now(summarize(d));
	}

	repeatLast(): void {
		this.announcer.now(this.lastSpoken || 'Nothing has been announced yet.');
	}

	cycleVerbosity(): void {
		const order = ['all', 'important', 'quiet'] as const;
		const next = order[(order.indexOf(prefs.value.verbosity) + 1) % order.length];
		prefs.update({ verbosity: next });
		this.pushSettings();
		const words = { all: 'Announce every change.', important: 'Announce important changes only.', quiet: 'Quiet. Only changes where you are.' };
		this.announcer.now(words[next]);
	}

	private onPointer(x: number, y: number): void {
		this.pointer = { x, y };
		const now = performance.now();
		if (now - this.pointerSentAt < POINTER_SEND_MS) return;
		this.pointerSentAt = now;
		this.engine.send({ type: 'pointer', xy: { x, y } });
	}

	private onShareEnded(): void {
		this.engine.stop();
		this.announcer.clear();
		this.phase = 'stopped';
		this.status = 'Sharing ended. The last version stays on the page. Press Start to read again.';
		this.shout('Sharing ended. Press Start to read again.');
	}

	private onConnection(state: ConnectionState, detail?: string): void {
		this.connection = state;
		if (state === 'open' && this.phase === 'reading') this.pushSettings();
		if (state === 'reconnecting' && this.phase === 'reading') {
			this.status = detail ?? 'Reconnecting to the reading engine.';
		} else if (state === 'open' && this.phase === 'reading' && this.doc.doc) {
			this.status = 'Reconnected. Reading continues.';
		}
	}

	private markChanged(refs: string[], version: number): void {
		if (refs.length === 0) return;
		const next = { ...this.changed };
		for (const r of refs) next[r] = version;
		this.changed = next;
	}

	private onMessage(msg: ServerMessage): void {
		switch (msg.type) {
			case 'snapshot':
				this.doc.snapshot(msg);
				this.status = `${this.phase === 'recording' ? 'Recorded' : 'Reading'}: ${summarize(msg.doc)}.`;
				break;
			case 'patch':
				if (!this.doc.patch(msg)) {
					this.engine.send({ type: 'hello', client: 'unscreen-web', caps: { webp: true, max_width: 1920 }, resume_version: -1 });
				}
				break;
			case 'announce':
				this.onAnnounce(msg);
				break;
			case 'status':
				this.busy = msg.stage === 'reconstruct';
				if (msg.stage === 'busy') this.status = 'Content unchanged, engine busy. The last version stays on the page.';
				else if (msg.stage === 'idle' && this.doc.doc && this.phase === 'reading') {
					this.status = `Reading: ${summarize(this.doc.doc)}.`;
				}
				break;
			case 'error':
				if (msg.code === 'engine_busy') this.shout(msg.message);
				else if (msg.code !== 'rate_limited') this.status = msg.message;
				break;
			case 'pointer_target':
				if (this.phase === 'reading' && this.pointer === null) break;
				this.pointerText = msg.text;
				this.pointerRef = msg.ref;
				if (this.pointerAsked) {
					this.pointerAsked = false;
					this.announcer.now(msg.text);
				}
				break;
			case 'answer':
				this.answers = [{ q: msg.q, text: msg.text, refs: msg.refs, version: msg.version }, ...this.answers].slice(0, 20);
				this.announcer.now(`Answer: ${msg.text}`);
				break;
		}
	}

	private onAnnounce(msg: Announce): void {
		const sentAt = this.frameSentAt[msg.version - 1];
		if (sentAt !== undefined) {
			this.lastLatencyMs = Math.round(performance.now() - sentAt);
			delete this.frameSentAt[msg.version - 1];
		}
		this.markChanged(msg.refs, msg.version);
		this.doc.record(msg.text);
		this.announcer.push(msg);
	}
}

export function summarize(d: { content_type: string; title: string | null; sheet: { rows: unknown[]; columns: unknown[] } | null; code: { lines: unknown[]; file_name: string | null } | null; blocks: unknown[] | null }): string {
	const title = d.title ? `, '${d.title}'` : '';
	if (d.content_type === 'sheet' && d.sheet) return `Spreadsheet${title}, ${d.sheet.rows.length} rows, ${d.sheet.columns.length} columns`;
	if (d.content_type === 'code' && d.code) return `Code${d.code.file_name ? `, '${d.code.file_name}'` : title}, ${d.code.lines.length} lines`;
	const n = d.blocks?.length ?? 0;
	const kind = d.content_type === 'slide' ? 'Slide' : d.content_type === 'doc' ? 'Document' : 'Unrecognised content';
	return `${kind}${title}, ${n} ${n === 1 ? 'block' : 'blocks'}`;
}
