import { createRng, type Rng } from './rng.ts';

export type CodeFixture = {
	seed: number;
	fileName: string;
	language: string;
	lines: string[];
	cursor: { line: number; col: number };
	theme: 'dark' | 'light';
	fontPx: number;
};

type Template = { fileName: string; language: string; body: (v: Vars) => string };
type Vars = { a: string; b: string; c: string; n: number; m: number; s: string };

const TEMPLATES: readonly Template[] = [
	{
		fileName: 'rate_limit.py',
		language: 'python',
		body: (v) => `import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    capacity: int = ${v.n}
    refill_per_s: float = ${v.m}.0
    tokens: float = field(init=False)
    updated: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()

    def allow(self, cost: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated
        self.updated = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_s)
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True


def ${v.a}(buckets: dict[str, TokenBucket], ${v.b}: str) -> bool:
    bucket = buckets.setdefault(${v.b}, TokenBucket())
    return bucket.allow()`
	},
	{
		fileName: 'useDebounce.ts',
		language: 'typescript',
		body: (v) => `import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delayMs = ${v.n * 10}): T {
  const [${v.a}, set${cap(v.a)}] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => set${cap(v.a)}(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return ${v.a};
}

export function ${v.b}(query: string): string[] {
  const ${v.c} = useDebounce(query, ${v.m * 50});
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    if (!${v.c}) return setResults([]);
    fetch(\`/api/search?q=\${encodeURIComponent(${v.c})}\`)
      .then((r) => r.json())
      .then(setResults)
      .catch(() => setResults([]));
  }, [${v.c}]);

  return results;
}`
	},
	{
		fileName: 'queue.go',
		language: 'go',
		body: (v) => `package jobs

import (
	"context"
	"errors"
	"time"
)

var ErrClosed = errors.New("queue closed")

type Job struct {
	ID       string
	Attempts int
	Payload  []byte
}

type Queue struct {
	items  chan Job
	closed bool
}

func New${cap(v.a)}(size int) *Queue {
	return &Queue{items: make(chan Job, size)}
}

func (q *Queue) Push(ctx context.Context, j Job) error {
	if q.closed {
		return ErrClosed
	}
	select {
	case q.items <- j:
		return nil
	case <-time.After(${v.n} * time.Millisecond):
		return context.DeadlineExceeded
	case <-ctx.Done():
		return ctx.Err()
	}
}

const MaxAttempts = ${v.m}`
	},
	{
		fileName: 'grades.py',
		language: 'python',
		body: (v) => `from statistics import mean

PASS_MARK = ${v.n}
WEIGHTS = {"quiz": 0.${v.m}, "midterm": 0.3, "final": 0.5}


def weighted_score(${v.a}: dict[str, float]) -> float:
    total = 0.0
    for part, weight in WEIGHTS.items():
        total += ${v.a}.get(part, 0.0) * weight
    return round(total, 2)


def ${v.b}(roster: list[dict[str, float]]) -> dict[str, int]:
    scores = [weighted_score(s) for s in roster]
    passed = sum(1 for s in scores if s >= PASS_MARK)
    return {
        "count": len(scores),
        "passed": passed,
        "failed": len(scores) - passed,
        "average": int(mean(scores)) if scores else 0,
    }


if __name__ == "__main__":
    print(${v.b}([{"quiz": 80, "midterm": 72, "final": 65}]))`
	},
	{
		fileName: 'server.ts',
		language: 'typescript',
		body: (v) => `import express from 'express';

const app = express();
const PORT = Number(process.env.PORT ?? ${v.n * 100});
const ${v.a} = new Map<string, number>();

app.use(express.json({ limit: '${v.m}kb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true, uptime: process.uptime() });
});

app.post('/count/:${v.b}', (req, res) => {
  const key = req.params.${v.b};
  const next = (${v.a}.get(key) ?? 0) + 1;
  ${v.a}.set(key, next);
  res.status(201).json({ key, count: next });
});

app.use((err: Error, _req: express.Request, res: express.Response) => {
  console.error(err);
  res.status(500).json({ error: '${v.s}' });
});

app.listen(PORT, () => console.log(\`listening on \${PORT}\`));`
	},
	{
		fileName: 'matrix.c',
		language: 'c',
		body: (v) => `#include <stdio.h>
#include <stdlib.h>

#define N ${v.n}

typedef struct {
    int rows;
    int cols;
    double *data;
} Matrix;

Matrix ${v.a}(int rows, int cols) {
    Matrix m = {rows, cols, calloc(rows * cols, sizeof(double))};
    return m;
}

void ${v.b}(const Matrix *a, const Matrix *b, Matrix *out) {
    for (int i = 0; i < a->rows; i++) {
        for (int j = 0; j < b->cols; j++) {
            double sum = 0.0;
            for (int k = 0; k < a->cols; k++) {
                sum += a->data[i * a->cols + k] * b->data[k * b->cols + j];
            }
            out->data[i * out->cols + j] = sum;
        }
    }
}

int main(void) {
    Matrix a = ${v.a}(N, N);
    printf("%d x %d\\n", a.rows, a.cols);
    free(a.data);
    return ${v.m % 2};
}`
	}
];

const NAMES = ['check', 'allowRequest', 'resolve', 'tally', 'summarize', 'store', 'cache', 'build', 'merge'];
const PARAMS = ['client_id', 'userId', 'key', 'term', 'slug', 'name', 'token'];
const LOCALS = ['debounced', 'current', 'pending', 'latest', 'settled'];
const MESSAGES = ['internal error', 'something broke', 'try again later', 'server error'];

function cap(s: string): string {
	return s.charAt(0).toUpperCase() + s.slice(1);
}

function vars(rng: Rng): Vars {
	return {
		a: rng.pick(NAMES),
		b: rng.pick(PARAMS),
		c: rng.pick(LOCALS),
		n: rng.int(2, 60),
		m: rng.int(2, 9),
		s: rng.pick(MESSAGES)
	};
}

export function generateCode(seed: number): CodeFixture {
	const rng = createRng(seed);
	const t = TEMPLATES[seed % TEMPLATES.length];
	const lines = t.body(vars(rng)).split('\n');
	return {
		seed,
		fileName: t.fileName,
		language: t.language,
		lines,
		cursor: { line: rng.int(0, lines.length - 1), col: 4 },
		theme: rng.chance(0.75) ? 'dark' : 'light',
		fontPx: rng.int(13, 16)
	};
}

export type CodeEdit =
	| { kind: 'replace'; line: number; text: string }
	| { kind: 'insert'; line: number; text: string }
	| { kind: 'delete'; line: number }
	| { kind: 'cursor'; line: number };

const INSERTS = ['# TODO: handle retries', '// TODO: add metrics', 'const DEBUG = false;', 'return nil'];

export function nextCodeEdit(fixture: CodeFixture, rng: Rng): CodeEdit {
	const roll = rng.next();
	const candidates = fixture.lines
		.map((text, i) => ({ text, i }))
		.filter((l) => /\d/.test(l.text) && l.text.trim().length > 0);
	if (roll < 0.5 && candidates.length > 0) {
		const target = rng.pick(candidates);
		const text = target.text.replace(/\d+/, String(rng.int(2, 999)));
		return { kind: 'replace', line: target.i, text };
	}
	if (roll < 0.7) {
		const line = rng.int(1, fixture.lines.length - 1);
		const indent = fixture.lines[line].match(/^\s*/)?.[0] ?? '';
		return { kind: 'insert', line, text: indent + rng.pick(INSERTS) };
	}
	if (roll < 0.8 && fixture.lines.length > 12) {
		const blank = fixture.lines.findIndex((l) => l.trim() === '');
		if (blank > 0) return { kind: 'delete', line: blank };
	}
	return { kind: 'cursor', line: rng.int(0, fixture.lines.length - 1) };
}

export function applyCodeEdit(fixture: CodeFixture, edit: CodeEdit): void {
	if (edit.kind === 'replace') fixture.lines[edit.line] = edit.text;
	else if (edit.kind === 'insert') fixture.lines.splice(edit.line, 0, edit.text);
	else if (edit.kind === 'delete') fixture.lines.splice(edit.line, 1);
	fixture.cursor = { line: Math.min(edit.line, fixture.lines.length - 1), col: 4 };
}
