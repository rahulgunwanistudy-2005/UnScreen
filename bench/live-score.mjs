export const norm = (s) => String(s ?? '').replace(/\s+/g, ' ').trim().toLowerCase();
const valueAtEnd = (text, value) => {
	const escaped = norm(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	return escaped.length > 0 && new RegExp(`(?:to |: )${escaped}\\.?$`).test(text);
};

// A row/column mention alone is not a correct change: require its new value, or an
// explicit uncertainty warning. Match only before the next edit of the same target.
export function matches(change, msg) {
	const text = norm(msg.text);
	const unclear = msg.kind === 'uncertain';
	if (change.kind === 'cell') return text.includes(norm(change.row)) && text.includes(norm(change.col)) && (unclear || valueAtEnd(text, change.new || 'blank'));
	if (change.kind === 'row_added') return msg.kind === 'row_added' && text.includes(norm(change.row));
	if (change.kind === 'row_removed') return msg.kind === 'row_removed' && text.includes(norm(change.row));
	if (change.kind === 'line') return new RegExp(`\\bline ${change.n}(?:\\s|:)`).test(text) && (unclear || valueAtEnd(text, change.new || 'blank line'));
	if (change.kind === 'lines') return (change.delta > 0 ? msg.kind === 'lines_added' : msg.kind === 'lines_removed') &&
		(Array.isArray(msg.refs) ? msg.refs.length === Math.abs(change.delta) : new RegExp(`^${Math.abs(change.delta)} lines? `).test(text));
	return false;
}

export function sameTarget(a, b) {
	if (a.kind !== b.kind) return false;
	if (a.kind === 'cell') return a.row === b.row && a.col === b.col;
	if (a.kind === 'line') return a.n === b.n;
	return a.row === b.row;
}

export function scoreChanges(changes, announces, spoken) {
	const used = new Set();
	const rows = changes.map((change, i) => {
		const next = changes.slice(i + 1).find((c) => sameTarget(change, c));
		const index = announces.findIndex((a, j) => !used.has(j) && a.at >= change.at && (!next || a.at < next.at) && matches(change, a));
		const hit = index >= 0 ? announces[index] : null;
		if (hit) used.add(index);
		const speech = hit && spoken.find((s) => s.at >= hit.at && (!next || s.at < next.at) && norm(s.text).includes(norm(hit.text)));
		return { ...change, announced: !!hit, spoken: !!speech, unclear: hit ? hit.kind === 'uncertain' : null,
			latency_ms: speech ? speech.at - change.at : null, engine_latency_ms: hit ? hit.at - change.at : null, text: hit?.text ?? null };
	});
	const content = announces.filter((a) => a.kind !== 'content_type' && a.kind !== 'title' && a.kind !== 'status');
	return { rows, recall: rows.length ? rows.filter((r) => r.announced).length / rows.length : null,
		spoken_recall: rows.length ? rows.filter((r) => r.spoken).length / rows.length : null,
		precision: content.length ? [...used].filter((i) => content.includes(announces[i])).length / content.length : null };
}
