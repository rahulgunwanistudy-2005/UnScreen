export type FixtureParams = {
	seed: number;
	live: boolean;
	frame: 'plain' | 'meet';
	intervalMs: number;
	rows?: number;
	cols?: number;
	cursor: boolean;
};

export function readParams(url: { searchParams: { get(key: string): string | null } }): FixtureParams {
	const num = (key: string) => {
		const raw = url.searchParams.get(key);
		const v = raw === null ? NaN : Number(raw);
		return Number.isFinite(v) ? v : undefined;
	};
	return {
		seed: num('seed') ?? 1,
		live: url.searchParams.get('mode') !== 'static',
		frame: url.searchParams.get('frame') === 'meet' ? 'meet' : 'plain',
		intervalMs: Math.max(500, num('interval') ?? 8000),
		rows: num('rows'),
		cols: num('cols'),
		cursor: url.searchParams.get('cursor') !== 'off'
	};
}
