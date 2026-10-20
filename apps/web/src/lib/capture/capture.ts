import type { WorkerIn, WorkerOut } from './capture.worker.ts';

export type CaptureEvents = {
	frame(out: Extract<WorkerOut, { kind: 'frame' }>): void;
	pointer(x: number, y: number): void;
	ended(): void;
	cpu(ms: number): void;
};

export class CaptureError extends Error {
	constructor(
		message: string,
		readonly reason: 'denied' | 'unsupported' | 'failed'
	) {
		super(message);
	}
}

const INTERVAL_MS = 500;

/**
 * Grabs the shared tab or window at 2 fps. Frames are copied on the main thread with
 * createImageBitmap (works in every Chromium, Firefox and Safari) and hashed and encoded in a
 * worker. A timer is used rather than requestVideoFrameCallback because tab capture only
 * produces frames when the tab repaints, and we still want a fresh look after stillness.
 */
export class ScreenCapture {
	private stream: MediaStream | null = null;
	private video: HTMLVideoElement | null = null;
	private worker: Worker | null = null;
	private timer: ReturnType<typeof setInterval> | null = null;
	private busy = false;
	surface: string | null = null;

	constructor(private events: CaptureEvents) {}

	get active(): boolean {
		return this.stream !== null;
	}

	async start(): Promise<void> {
		if (!navigator.mediaDevices?.getDisplayMedia) {
			throw new CaptureError('This browser cannot share a tab or window. Use Chrome, Edge or Firefox on a computer.', 'unsupported');
		}
		const controller = typeof CaptureController === 'function' ? new CaptureController() : undefined;
		try {
			this.stream = await navigator.mediaDevices.getDisplayMedia({
				video: { frameRate: { ideal: 5, max: 10 }, displaySurface: 'browser' },
				audio: false,
				...(controller ? { controller } : {}),
				selfBrowserSurface: 'exclude',
				surfaceSwitching: 'include',
				monitorTypeSurfaces: 'include'
			} as DisplayMediaStreamOptions);
		} catch (err) {
			const name = err instanceof DOMException ? err.name : '';
			if (name === 'NotAllowedError') {
				throw new CaptureError('Sharing was cancelled or blocked. Press Start and choose the meeting tab or window.', 'denied');
			}
			throw new CaptureError('Could not start screen capture. Try again, or reload the page.', 'failed');
		}
		const [track] = this.stream.getVideoTracks();
		this.surface = (track.getSettings() as MediaTrackSettings & { displaySurface?: string }).displaySurface ?? null;
		// Keep the screen reader on UnScreen instead of jumping to the shared tab.
		try {
			(controller as (CaptureController & { setFocusBehavior?(b: string): void }) | undefined)?.setFocusBehavior?.(
				'no-focus-change'
			);
		} catch {
			// Not supported for this surface (e.g. a whole screen); nothing to do.
		}
		track.addEventListener('ended', () => {
			this.stop();
			this.events.ended();
		});

		this.video = document.createElement('video');
		this.video.muted = true;
		this.video.playsInline = true;
		this.video.srcObject = this.stream;
		await this.video.play();

		this.worker = new Worker(new URL('./capture.worker.ts', import.meta.url), { type: 'module' });
		this.worker.onmessage = (ev: MessageEvent<WorkerOut>) => {
			this.busy = false;
			const out = ev.data;
			if (out.kind !== 'error') this.events.cpu(out.cpuMs);
			if (out.kind === 'frame') this.events.frame(out);
			else if (out.kind === 'pointer') this.events.pointer(out.x, out.y);
		};
		this.timer = setInterval(() => void this.tick(), INTERVAL_MS);
	}

	/** Ask the worker to send the next stable frame even if nothing changed (after reconnect). */
	resend(): void {
		this.post({ kind: 'invalidate' });
	}

	private post(msg: WorkerIn, transfer: Transferable[] = []): void {
		this.worker?.postMessage(msg, transfer);
	}

	private async tick(): Promise<void> {
		const video = this.video;
		if (!video || this.busy || video.videoWidth === 0) return;
		this.busy = true;
		try {
			const bitmap = await createImageBitmap(video);
			this.post({ kind: 'frame', bitmap, now: performance.now(), maxWidth: 1920 }, [bitmap]);
		} catch {
			this.busy = false;
		}
	}

	stop(): void {
		if (this.timer) clearInterval(this.timer);
		this.timer = null;
		this.worker?.terminate();
		this.worker = null;
		this.stream?.getTracks().forEach((t) => t.stop());
		this.stream = null;
		if (this.video) this.video.srcObject = null;
		this.video = null;
		this.busy = false;
	}
}
