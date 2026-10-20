import { createRng, type Rng } from './rng.ts';

export type ColumnKind = 'name' | 'money' | 'percent' | 'int' | 'date' | 'status' | 'person' | 'code';

export type SheetColumn = { header: string; kind: ColumnKind };

export type SheetStyle = {
	theme: 'light' | 'dark';
	fontPx: number;
	zebra: boolean;
	boldHeader: boolean;
	gridlines: boolean;
	headerFill: string;
	font: string;
};

export type SheetFixture = {
	seed: number;
	title: string;
	sheetName: string;
	columns: SheetColumn[];
	rows: string[][];
	style: SheetStyle;
};

type Topic = {
	title: string;
	sheetName: string;
	key: { header: string; values: readonly string[] };
	columns: readonly SheetColumn[];
};

const COMPANIES = [
	'Acme Corp', 'Globex', 'Initech', 'Umbrella Health', 'Hooli', 'Vandelay Imports', 'Stark Labs',
	'Wayne Freight', 'Soylent Foods', 'Tyrell Systems', 'Cyberdyne', 'Wonka Retail', 'Pied Piper',
	'Gringotts Bank', 'Oscorp', 'Nakatomi Trading', 'Monarch Solar', 'Blue Sun', 'Duff Brewing',
	'Krusty Kitchens', 'Massive Dynamic', 'Aperture Optics'
] as const;
const PEOPLE = [
	'Asha Rao', 'Ben Okafor', 'Chen Wei', 'Diya Menon', 'Elif Kaya', 'Farah Haddad', 'Gabe Silva',
	'Hana Sato', 'Ivan Petrov', 'Jaya Iyer', 'Kofi Mensah', 'Lena Fischer', 'Mateo Ruiz', 'Nia Brooks',
	'Omar Aziz', 'Priya Nair', 'Quinn Lee', 'Rhea Kapoor', 'Sam Ortiz', 'Tara Singh', 'Uma Das',
	'Victor Hugo', 'Wen Zhao', 'Yusuf Ali'
] as const;
const COURSES = [
	'Data Structures', 'Operating Systems', 'Linear Algebra', 'Compilers', 'Signals', 'Databases',
	'Networks', 'Probability', 'Thermodynamics', 'Microeconomics', 'Organic Chemistry', 'Ethics',
	'Discrete Maths', 'Control Systems', 'Machine Learning', 'Graph Theory', 'Optics', 'Genetics'
] as const;
const ITEMS = [
	'USB-C cable', 'Laptop stand', 'Monitor 27in', 'Webcam HD', 'Desk lamp', 'Keyboard', 'Mouse',
	'Headset', 'Docking station', 'Router', 'SSD 1TB', 'Ethernet 5m', 'Power strip', 'Whiteboard',
	'Marker set', 'Label printer', 'Chair mat', 'Cable ties', 'Projector', 'Stylus pen'
] as const;
const TASKS = [
	'Fix login timeout', 'Migrate CI runners', 'Add CSV export', 'Refactor auth', 'Dark mode toggle',
	'Rate limit API', 'Update privacy page', 'Search indexing', 'Retry webhooks', 'Cache warmup',
	'Audit logging', 'Onboarding emails', 'Bulk invite', 'Localise dates', 'Crash on resume',
	'Billing alerts', 'SSO for admins', 'Reduce bundle size'
] as const;
const SAMPLES = [
	'S-101', 'S-102', 'S-103', 'S-104', 'S-105', 'S-106', 'S-107', 'S-108', 'S-109', 'S-110',
	'S-111', 'S-112', 'S-113', 'S-114', 'S-115', 'S-116', 'S-117', 'S-118', 'S-119', 'S-120'
] as const;

const TOPICS: readonly Topic[] = [
	{
		title: 'Q3 Pipeline',
		sheetName: 'Pipeline',
		key: { header: 'Account', values: COMPANIES },
		columns: [
			{ header: 'Owner', kind: 'person' },
			{ header: 'Stage', kind: 'status' },
			{ header: 'Q3 revenue', kind: 'money' },
			{ header: 'Q4 forecast', kind: 'money' },
			{ header: 'Win rate', kind: 'percent' },
			{ header: 'Close date', kind: 'date' },
			{ header: 'Seats', kind: 'int' }
		]
	},
	{
		title: 'Midterm grades',
		sheetName: 'Grades',
		key: { header: 'Student', values: PEOPLE },
		columns: [
			{ header: 'Roll no', kind: 'code' },
			{ header: 'Quiz 1', kind: 'int' },
			{ header: 'Quiz 2', kind: 'int' },
			{ header: 'Midterm', kind: 'int' },
			{ header: 'Attendance', kind: 'percent' },
			{ header: 'Status', kind: 'status' }
		]
	},
	{
		title: 'Lab inventory',
		sheetName: 'Stock',
		key: { header: 'Item', values: ITEMS },
		columns: [
			{ header: 'SKU', kind: 'code' },
			{ header: 'In stock', kind: 'int' },
			{ header: 'Unit cost', kind: 'money' },
			{ header: 'Reorder by', kind: 'date' },
			{ header: 'Supplier', kind: 'name' },
			{ header: 'Status', kind: 'status' }
		]
	},
	{
		title: 'Sprint 42 tracker',
		sheetName: 'Sprint',
		key: { header: 'Task', values: TASKS },
		columns: [
			{ header: 'Assignee', kind: 'person' },
			{ header: 'Points', kind: 'int' },
			{ header: 'Status', kind: 'status' },
			{ header: 'Due', kind: 'date' },
			{ header: 'Ticket', kind: 'code' }
		]
	},
	{
		title: 'Course budget',
		sheetName: 'Budget',
		key: { header: 'Course', values: COURSES },
		columns: [
			{ header: 'Instructor', kind: 'person' },
			{ header: 'Credits', kind: 'int' },
			{ header: 'Lab fee', kind: 'money' },
			{ header: 'Pass rate', kind: 'percent' },
			{ header: 'Exam date', kind: 'date' }
		]
	},
	{
		title: 'Assay results',
		sheetName: 'Run 7',
		key: { header: 'Sample', values: SAMPLES },
		columns: [
			{ header: 'Operator', kind: 'person' },
			{ header: 'Yield', kind: 'percent' },
			{ header: 'Volume ml', kind: 'int' },
			{ header: 'Cost', kind: 'money' },
			{ header: 'Run date', kind: 'date' },
			{ header: 'QC', kind: 'status' }
		]
	}
];

const STATUSES: Record<string, readonly string[]> = {
	Stage: ['Prospect', 'Qualified', 'Proposal', 'Negotiation', 'Closed won', 'Closed lost'],
	Status: ['Open', 'In progress', 'Blocked', 'Done', 'Pass', 'Review'],
	QC: ['Pass', 'Fail', 'Retest', 'Pending']
};
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const SUPPLIERS = ['Northwind', 'Contoso', 'Fabrikam', 'Tailspin', 'Litware', 'Proseware'];
const FONTS = [
	'Arial, Helvetica, sans-serif',
	'"Roboto", "Segoe UI", Arial, sans-serif',
	'Verdana, Geneva, sans-serif',
	'"Times New Roman", Times, serif',
	'Calibri, Carlito, "Segoe UI", sans-serif'
];
const FILLS_LIGHT = ['#e8eaed', '#dbe8fb', '#e6f4ea', '#fdecc8', '#f3e8fd'];
const FILLS_DARK = ['#3c4043', '#1f3a5f', '#20402c', '#4a3a12', '#3b2a52'];

export function cellValue(rng: Rng, column: SheetColumn): string {
	switch (column.kind) {
		case 'money': {
			const v = rng.int(5, 2400) * (rng.chance(0.5) ? 100 : 1);
			return rng.chance(0.25) ? `$${(v / 1000).toFixed(1)}K` : `$${v.toLocaleString('en-US')}`;
		}
		case 'percent':
			return `${rng.int(3, 99)}%`;
		case 'int':
			return String(rng.int(0, column.header.startsWith('Quiz') ? 20 : 480));
		case 'date':
			return `${rng.int(1, 28)} ${rng.pick(MONTHS)} 2026`;
		case 'status':
			return rng.pick(STATUSES[column.header] ?? STATUSES.Status);
		case 'person':
			return rng.pick(PEOPLE);
		case 'code':
			return `${rng.pick(['AX', 'BT', 'CR', 'DL', 'EN'])}-${rng.int(100, 9999)}`;
		case 'name':
			return rng.pick(SUPPLIERS);
	}
}

export type SheetOptions = { rows?: number; cols?: number };

export function generateSheet(seed: number, options: SheetOptions = {}): SheetFixture {
	const rng = createRng(seed);
	const topic = TOPICS[seed % TOPICS.length];
	const colCount = Math.min(options.cols ?? rng.int(4, topic.columns.length), topic.columns.length);
	const columns: SheetColumn[] = [
		{ header: topic.key.header, kind: 'name' },
		...topic.columns.slice(0, colCount)
	];
	const rowCount = Math.min(options.rows ?? rng.int(6, 16), topic.key.values.length);
	const keys = rng.shuffle(topic.key.values).slice(0, rowCount);
	const rows = keys.map((key) => [key, ...columns.slice(1).map((c) => cellValue(rng, c))]);
	const theme = rng.chance(0.3) ? 'dark' : 'light';
	return {
		seed,
		title: topic.title,
		sheetName: topic.sheetName,
		columns,
		rows,
		style: {
			theme,
			fontPx: rng.int(12, 15),
			zebra: rng.chance(0.5),
			boldHeader: rng.chance(0.8),
			gridlines: rng.chance(0.85),
			headerFill: rng.pick(theme === 'dark' ? FILLS_DARK : FILLS_LIGHT),
			font: rng.pick(FONTS)
		}
	};
}

export type SheetEdit =
	| { kind: 'cell'; row: number; col: number; value: string }
	| { kind: 'add_row'; at: number; values: string[] }
	| { kind: 'scroll'; by: number };

/** Next scripted edit. Keys never repeat so row identity stays well defined. */
export function nextSheetEdits(fixture: SheetFixture, rng: Rng): SheetEdit[] {
	if (rng.chance(0.1)) {
		const used = new Set(fixture.rows.map((r) => r[0]));
		const topic = TOPICS[fixture.seed % TOPICS.length];
		const fresh = topic.key.values.filter((k) => !used.has(k));
		if (fresh.length > 0) {
			const values = [rng.pick(fresh), ...fixture.columns.slice(1).map((c) => cellValue(rng, c))];
			return [{ kind: 'add_row', at: fixture.rows.length, values }];
		}
	}
	const n = rng.int(1, 3);
	const edits: SheetEdit[] = [];
	for (let i = 0; i < n; i++) {
		const row = rng.int(0, fixture.rows.length - 1);
		const col = rng.int(1, fixture.columns.length - 1);
		edits.push({ kind: 'cell', row, col, value: cellValue(rng, fixture.columns[col]) });
	}
	return edits;
}

export function applySheetEdit(fixture: SheetFixture, edit: SheetEdit): void {
	if (edit.kind === 'cell') fixture.rows[edit.row][edit.col] = edit.value;
	else if (edit.kind === 'add_row') fixture.rows.splice(edit.at, 0, edit.values);
}
