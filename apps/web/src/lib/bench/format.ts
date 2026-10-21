import summary from './summary.json';

export type Pool = {
	frames: number;
	items: number;
	exact_match: number;
	cer: number;
	hallucination_rate: number;
	structure_accuracy: number;
	text_recall: number;
	flagged: number;
	flagged_wrong: number;
};

export type Aggregate = {
	unscreen: Pool;
	ocr: Pool;
	ocr_config?: string;
	content_type_accuracy: number;
	errors: number;
	latency_ms: { p50: number | null; p95: number | null; max: number | null };
	cost_usd_per_frame: number | null;
	calls_per_frame: number | null;
};

export type Run = {
	file: string;
	run_at: string;
	models: Record<string, string | boolean>;
	overall: Aggregate;
	groups: Record<string, Aggregate>;
	frames: number;
};

export type LiveRun = {
	file: string;
	run_at: string;
	kind: string;
	edit_interval_ms: number;
	first_snapshot_ms: number | null;
	truth_changes: number;
	recall: number | null;
	precision: number | null;
	change_to_announce_ms: { p50: number | null; p95: number | null; n: number };
	final_dom_vs_truth: { ok: number; total: number } | null;
	engine_errors: number;
	never_read: boolean;
};

export type Pipeline = { file: string; run_at: string; note: string; edits: number; latencies_ms: number[]; p50_ms: number; max_ms: number };

export const bench = summary as { full?: Run; kill?: Run; live?: LiveRun[]; pipeline?: Pipeline };

/** The headline run: the full benchmark when it exists, otherwise the Day-1 kill test. */
export const headline: { run: Run; label: string } | null = bench.full
	? { run: bench.full, label: 'full benchmark' }
	: bench.kill
		? { run: bench.kill, label: 'kill test' }
		: null;

export const pct = (v: number | null | undefined, digits = 1) =>
	v === null || v === undefined || Number.isNaN(v) ? 'not measured' : `${(v * 100).toFixed(digits)}%`;

export const secs = (ms: number | null | undefined) =>
	ms === null || ms === undefined ? 'not measured' : `${(ms / 1000).toFixed(1)} s`;

export const date = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
