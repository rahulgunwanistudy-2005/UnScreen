// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};

declare global {
	/** Screen Capture API (Chrome 109+); not yet in TypeScript's DOM lib. */
	class CaptureController {
		constructor();
		setFocusBehavior(behavior: 'focus-captured-surface' | 'no-focus-change'): void;
	}
}
