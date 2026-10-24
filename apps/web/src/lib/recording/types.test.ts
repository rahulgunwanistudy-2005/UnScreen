import { describe, expect, it } from 'vitest';
import recorded from '../../../static/recordings/session.json';
import { readRecording } from './types.ts';

describe('recorded real-model session', () => {
	it('loads the packaged genuine run and rejects invalid or unsorted playback', () => {
		const valid = readRecording(recorded);
		expect(valid.events[0].message.type).toBe('snapshot');
		expect(valid.events.some((e) => e.message.type === 'patch')).toBe(true);
		expect(() => readRecording({ ...recorded, events: [] })).toThrow();
		expect(() => readRecording({ ...recorded, events: [{ ...recorded.events[0], at: -1 }] })).toThrow();
	});
});
