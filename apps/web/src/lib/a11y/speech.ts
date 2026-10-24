/** Optional audible preview for sighted demos. Never enabled or persisted automatically. */
export class SpeechPreview {
	private enabled = false;

	setEnabled(enabled: boolean): void {
		this.enabled = enabled;
		if (!enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
	}

	say(text: string): void {
		if (!this.enabled || typeof speechSynthesis === 'undefined') return;
		speechSynthesis.cancel();
		speechSynthesis.speak(new SpeechSynthesisUtterance(text));
	}

	stop(): void {
		if (this.enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
	}
}
