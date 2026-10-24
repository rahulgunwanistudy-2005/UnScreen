import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scoreChanges } from './live-score.mjs';

test('wrong values and late announcements for superseded values do not score', () => {
	const c = { kind: 'cell', row: 'Acme', col: 'Revenue', old: '1', new: '$200' };
	const changes = [{ ...c, at: 0 }, { ...c, at: 100, new: '$300' }];
	const announces = [{ at: 50, kind: 'cell', text: 'Acme, Revenue: $900' }, { at: 150, kind: 'cell', text: 'Acme, Revenue: $200' }];
	const s = scoreChanges(changes, announces, []);
	assert.equal(s.recall, 0); assert.equal(s.precision, 0);
});

test('one announcement cannot count twice; latency ends at the live region', () => {
	const changes = [{ at: 0, kind: 'cell', row: 'Acme', col: 'Revenue', new: '$200' }];
	const announces = [{ at: 400, kind: 'cell', text: 'Acme, Revenue: $100 to $200.' }];
	const s = scoreChanges(changes, announces, [{ at: 1900, text: announces[0].text }]);
	assert.equal(s.recall, 1); assert.equal(s.precision, 1); assert.equal(s.rows[0].latency_ms, 1900);
});

test('an uncertainty warning detects a change without claiming its value', () => {
	const s = scoreChanges([{ at: 0, kind: 'cell', row: 'Acme', col: 'Revenue', new: '$200' }],
		[{ at: 5, kind: 'uncertain', text: 'Acme, Revenue: possibly changed, unclear.' }], []);
	assert.equal(s.recall, 1); assert.equal(s.rows[0].unclear, true); assert.equal(s.rows[0].latency_ms, null);
});

test('numeric prefixes and different line numbers are not correct matches', () => {
	assert.equal(scoreChanges([{ at: 0, kind: 'cell', row: 'Acme', col: 'Revenue', new: '$200' }],
		[{ at: 5, kind: 'cell', text: 'Acme, Revenue: $2000.' }], []).recall, 0);
	const change = { at: 0, kind: 'line', n: 2, new: 'x = 3' };
	assert.equal(scoreChanges([change], [{ at: 5, kind: 'line', text: 'Line 20 now reads: x = 3' }], []).recall, 0);
	assert.equal(scoreChanges([change], [{ at: 5, kind: 'line', text: 'Line 2 changed. Was: x = 1. Now: x = 3' }], []).recall, 1);
});

test('a desired value appearing only as the old value does not score', () => {
	assert.equal(scoreChanges([{ at: 0, kind: 'cell', row: 'Acme', col: 'Revenue', new: '$200' }],
		[{ at: 5, kind: 'cell', text: 'Acme, Revenue: $200 to $900.' }], []).recall, 0);
});

test('a single inserted line is matched by its reference count, not a digit in its label', () => {
	const c = { at: 0, kind: 'lines', delta: 1 };
	const a = { at: 5, kind: 'lines_added', refs: ['l7'], text: 'Line 7 added: return value' };
	assert.equal(scoreChanges([c], [a], []).recall, 1);
	assert.equal(scoreChanges([{ ...c, delta: 2 }], [a], []).recall, 0);
});
