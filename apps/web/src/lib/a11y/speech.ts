/** Optional audible preview for sighted demos. Never enabled or persisted automatically. */
export class SpeechPreview {
	private enabled = false;
	// Chrome can drop an utterance that is garbage-collected mid-speech, so keep a reference.
	private current: SpeechSynthesisUtterance | null = null;

	constructor(private onError: (message: string) => void = () => {}) {}

	setEnabled(enabled: boolean): void {
		this.enabled = enabled;
		if (!enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
	}

	say(text: string): void {
		if (!this.enabled || typeof speechSynthesis === 'undefined') return;
		// Chrome can drop an utterance queued straight after cancel(), so only cancel when busy.
		if (speechSynthesis.speaking || speechSynthesis.pending) speechSynthesis.cancel();
		// Chrome can be left paused after a cancel or while the tab is hidden; speech then stays silent.
		speechSynthesis.resume();
		const utterance = new SpeechSynthesisUtterance(text);
		utterance.lang = document.documentElement.lang || 'en';
		const voice = pickVoice(utterance.lang);
		if (voice) utterance.voice = voice;
		utterance.onerror = (e) => {
			if (e.error !== 'interrupted' && e.error !== 'canceled') this.onError(describeError(e.error));
		};
		this.current = utterance;
		speechSynthesis.speak(utterance);
	}

	stop(): void {
		if (this.enabled && typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
		this.current = null;
	}
}

/** The default voice when it speaks the page language, else the first local voice that does. */
function pickVoice(lang: string): SpeechSynthesisVoice | undefined {
	const prefix = lang.slice(0, 2).toLowerCase();
	const voices = speechSynthesis.getVoices().filter((v) => v.lang.toLowerCase().startsWith(prefix));
	return voices.find((v) => v.default) ?? voices.find((v) => v.localService) ?? voices[0];
}

function describeError(error: string): string {
	switch (error) {
		case 'not-allowed':
			return 'The browser blocked speech. Click anywhere on this page, then turn Hear it off and on again.';
		case 'audio-busy':
		case 'audio-hardware':
			return 'Speech could not reach an audio output. Check that this tab is not muted and a speaker is connected.';
		case 'synthesis-unavailable':
		case 'synthesis-failed':
		case 'voice-unavailable':
		case 'language-unavailable':
			return 'This browser has no working speech voice. Try Chrome or Safari, or install a system voice.';
		default:
			return `Speech failed (${error}).`;
	}
}
