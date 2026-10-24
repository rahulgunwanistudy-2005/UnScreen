/** Optional audible preview for sighted demos. Never enabled or persisted automatically. */
export class SpeechPreview {
	private enabled = false;

	setEnabled(enabled: boolean): void {
		this.enabled = enabled;
		if (!enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
	}

	say(text: string): void {
		if (!this.enabled || typeof speechSynthesis === 'undefined') return;
		// Chrome can drop an utterance queued straight after cancel(), so only cancel when busy.
		if (speechSynthesis.speaking || speechSynthesis.pending) speechSynthesis.cancel();
		speechSynthesis.speak(new SpeechSynthesisUtterance(text));
	}

	stop(): void {
		if (this.enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
	}
}
