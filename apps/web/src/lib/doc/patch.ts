import type { PatchOp } from '@unscreen/schema';

export class PatchError extends Error {}

function unescape(token: string): string {
	return token.replace(/~1/g, '/').replace(/~0/g, '~');
}

function parse(path: string): string[] {
	if (path === '') return [];
	if (!path.startsWith('/')) throw new PatchError(`bad path ${path}`);
	return path.slice(1).split('/').map(unescape);
}

type Container = Record<string, unknown> | unknown[];

function step(node: unknown, token: string, path: string): unknown {
	if (Array.isArray(node)) {
		const i = Number(token);
		if (!Number.isInteger(i) || i < 0 || i >= node.length) throw new PatchError(`no index ${token} in ${path}`);
		return node[i];
	}
	if (node !== null && typeof node === 'object' && token in node) return (node as Record<string, unknown>)[token];
	throw new PatchError(`no key ${token} in ${path}`);
}

/**
 * Apply RFC 6902 add/remove/replace operations in place. Mutating in place (rather than
 * rebuilding the document) is what lets Svelte update only the changed text nodes, so a
 * screen reader's position in the table survives every update.
 */
export function applyPatch(doc: Record<string, unknown>, ops: readonly PatchOp[]): void {
	for (const op of ops) {
		const tokens = parse(op.path);
		if (tokens.length === 0) throw new PatchError('cannot replace the document root');
		const last = tokens[tokens.length - 1];
		let parent: unknown = doc;
		for (const t of tokens.slice(0, -1)) parent = step(parent, t, op.path);
		if (parent === null || typeof parent !== 'object') throw new PatchError(`parent of ${op.path} is not a container`);
		const target = parent as Container;
		if (Array.isArray(target)) {
			const i = last === '-' ? target.length : Number(last);
			if (!Number.isInteger(i) || i < 0) throw new PatchError(`bad index in ${op.path}`);
			if (op.op === 'add') {
				if (i > target.length) throw new PatchError(`index out of range in ${op.path}`);
				target.splice(i, 0, op.value);
			} else if (op.op === 'remove') {
				if (i >= target.length) throw new PatchError(`index out of range in ${op.path}`);
				target.splice(i, 1);
			} else {
				if (i >= target.length) throw new PatchError(`index out of range in ${op.path}`);
				target[i] = op.value;
			}
		} else if (op.op === 'remove') {
			if (!(last in target)) throw new PatchError(`no key ${last} in ${op.path}`);
			delete target[last];
		} else {
			if (op.op === 'replace' && !(last in target)) throw new PatchError(`no key ${last} in ${op.path}`);
			target[last] = op.value;
		}
	}
}
