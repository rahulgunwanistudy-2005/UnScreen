import type { ServerMessage } from '../engine/client.ts';

export type RecordedSession = {
	schema_version: 1;
	source: string;
	recorded_at: string;
	playback_rate: number;
	models: Record<string, string>;
	events: { at: number; message: ServerMessage }[];
};

export function readRecording(data: unknown): RecordedSession {
	const r = data as Partial<RecordedSession> | null;
	if (!r || r.schema_version !== 1 || typeof r.source !== 'string' || typeof r.recorded_at !== 'string'
		|| !Array.isArray(r.events) || !r.events.length || r.events[0].message?.type !== 'snapshot'
		|| r.playback_rate !== 2 || !r.events.every((e, i, all) => Number.isFinite(e.at) && e.at >= 0
			&& (!i || e.at >= all[i - 1].at) && typeof e.message?.type === 'string')) {
		throw new Error('The recorded session could not be loaded.');
	}
	return r as RecordedSession;
}
