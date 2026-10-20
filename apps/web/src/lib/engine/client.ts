import type { ClientCaps, Frame, Hello, SessionGrant, UnScreenSchema } from '@unscreen/schema';

export type ServerMessage = UnScreenSchema['server_message'];
type ClientMessage = UnScreenSchema['client_message'];

export type ConnectionState = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed';

export type EngineHandlers = {
	message(msg: ServerMessage): void;
	state(state: ConnectionState, detail?: string): void;
	/** A new engine session started (first connect or after expiry); the client must resend a frame. */
	fresh(): void;
	resumeVersion(): number | null;
};

export type OutgoingFrame = { meta: Omit<Frame, 'type' | 'seq' | 'ts'>; data: Blob };

const BACKOFF_MS = [500, 1000, 2000, 4000, 8000, 10000];
const CAPS: ClientCaps = { webp: true, max_width: 1920 };

export function engineUrl(): string {
	const configured = import.meta.env.VITE_ENGINE_URL as string | undefined;
	return (configured || 'http://localhost:8787').replace(/\/$/, '');
}

/**
 * WebSocket client with reconnect-and-resume. At most one frame is in flight; while the
 * engine works, newer frames replace the queued one (latest wins).
 */
export class EngineClient {
	private ws: WebSocket | null = null;
	private grant: SessionGrant | null = null;
	private attempt = 0;
	private stopped = true;
	private inFlight = false;
	private pending: OutgoingFrame | null = null;
	private seq = 0;
	private retryTimer: ReturnType<typeof setTimeout> | null = null;

	constructor(
		private handlers: EngineHandlers,
		private base: string = engineUrl()
	) {}

	async start(): Promise<void> {
		this.stopped = false;
		this.attempt = 0;
		await this.connect();
	}

	stop(): void {
		this.stopped = true;
		if (this.retryTimer) clearTimeout(this.retryTimer);
		this.retryTimer = null;
		this.pending = null;
		this.inFlight = false;
		this.ws?.close(1000, 'stopped');
		this.ws = null;
		this.handlers.state('closed');
	}

	send(msg: Exclude<ClientMessage, Frame>): boolean {
		if (this.ws?.readyState !== WebSocket.OPEN) return false;
		this.ws.send(JSON.stringify(msg));
		return true;
	}

	sendFrame(frame: OutgoingFrame): void {
		if (this.inFlight || this.ws?.readyState !== WebSocket.OPEN) {
			this.pending = frame;
			return;
		}
		this.inFlight = true;
		const msg: Frame = { type: 'frame', seq: ++this.seq, ts: Date.now() / 1000, ...frame.meta };
		this.ws.send(JSON.stringify(msg));
		this.ws.send(frame.data);
	}

	private release(): void {
		this.inFlight = false;
		const next = this.pending;
		this.pending = null;
		if (next) this.sendFrame(next);
	}

	private async newSession(): Promise<SessionGrant> {
		const res = await fetch(`${this.base}/v1/session`, { method: 'POST' });
		if (res.status === 429) throw new Error('The reading engine is busy. Try again in a minute.');
		if (!res.ok) throw new Error(`The reading engine refused to start (${res.status}).`);
		return (await res.json()) as SessionGrant;
	}

	private async connect(): Promise<void> {
		this.handlers.state(this.attempt === 0 ? 'connecting' : 'reconnecting');
		let fresh = false;
		try {
			if (!this.grant) {
				this.grant = await this.newSession();
				fresh = true;
			}
		} catch (err) {
			this.scheduleRetry(err instanceof Error ? err.message : 'Cannot reach the reading engine.');
			return;
		}
		if (this.stopped) return;
		const url = `${this.base.replace(/^http/, 'ws')}/v1/session/${this.grant.session_id}/ws?token=${encodeURIComponent(this.grant.token)}`;
		const ws = new WebSocket(url);
		ws.binaryType = 'arraybuffer';
		this.ws = ws;
		ws.onopen = () => {
			this.attempt = 0;
			this.inFlight = false;
			const hello: Hello = {
				type: 'hello',
				client: 'unscreen-web',
				caps: CAPS,
				resume_version: fresh ? null : this.handlers.resumeVersion()
			};
			ws.send(JSON.stringify(hello));
			this.handlers.state('open');
			if (fresh) this.handlers.fresh();
			this.release();
		};
		ws.onmessage = (ev) => {
			if (typeof ev.data !== 'string') return;
			let msg: ServerMessage;
			try {
				msg = JSON.parse(ev.data) as ServerMessage;
			} catch {
				return;
			}
			if (msg.type === 'status' && msg.stage !== 'reconstruct') this.release();
			if (msg.type === 'error' && msg.code !== 'rate_limited') this.release();
			this.handlers.message(msg);
		};
		ws.onclose = (ev) => {
			if (this.ws !== ws) return;
			this.ws = null;
			if (this.stopped) return;
			if (ev.code === 4401) this.grant = null;
			this.scheduleRetry('Connection to the reading engine was lost. Reconnecting.');
		};
	}

	private scheduleRetry(detail: string): void {
		if (this.stopped) return;
		const delay = BACKOFF_MS[Math.min(this.attempt, BACKOFF_MS.length - 1)];
		this.attempt += 1;
		this.handlers.state('reconnecting', detail);
		this.retryTimer = setTimeout(() => void this.connect(), delay);
	}
}
