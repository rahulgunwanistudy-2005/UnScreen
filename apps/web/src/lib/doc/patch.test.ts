import { describe, expect, it } from 'vitest';
import { applyPatch, PatchError } from './patch.ts';

describe('applyPatch', () => {
	it('replaces, adds and removes in place without replacing containers', () => {
		const rows = [{ id: 'r1', text: 'a' }, { id: 'r2', text: 'b' }];
		const doc = { sheet: { rows } };
		const keep = rows[0];
		applyPatch(doc, [
			{ op: 'replace', path: '/sheet/rows/1/text', value: 'B' },
			{ op: 'add', path: '/sheet/rows/1', value: { id: 'r3', text: 'c' } },
			{ op: 'remove', path: '/sheet/rows/2', value: null }
		]);
		expect(doc.sheet.rows).toBe(rows);
		expect(doc.sheet.rows[0]).toBe(keep);
		expect(doc.sheet.rows.map((r) => r.id)).toEqual(['r1', 'r3']);
	});

	it('unescapes ~0 and ~1 and supports "-" append', () => {
		const doc: Record<string, unknown> = { 'a/b': 1, list: [1] };
		applyPatch(doc, [
			{ op: 'replace', path: '/a~1b', value: 2 },
			{ op: 'add', path: '/list/-', value: 2 },
			{ op: 'add', path: '/c~0d', value: true }
		]);
		expect(doc).toEqual({ 'a/b': 2, list: [1, 2], 'c~d': true });
	});

	it('rejects ops that do not fit the document', () => {
		expect(() => applyPatch({ a: [] }, [{ op: 'remove', path: '/a/0', value: null }])).toThrow(PatchError);
		expect(() => applyPatch({}, [{ op: 'replace', path: '/missing', value: 1 }])).toThrow(PatchError);
		expect(() => applyPatch({}, [{ op: 'replace', path: '', value: 1 }])).toThrow(PatchError);
	});
});
