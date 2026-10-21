# UnScreen

**Every screen share, readable by a screen reader, live.**

Zoom, Google Meet and Microsoft Teams send shared content as a picture, so a screen reader can only say that someone is sharing. UnScreen reads the shared tab or window, rebuilds it as a real table, code listing or outline, and announces what changed. It needs nothing from the presenter and works with NVDA, VoiceOver and ChromeVox in any meeting app.

Built for the Taskforge hackathon (October 17–24, 2026). All code in this repository was written during the event.

## The barrier

- Zoom, Meet and Teams all render shared content as an image to screen reader users (Leporini, Buzzi and Hersh, [ACM TACCESS 2023](https://dl.acm.org/doi/full/10.1145/3573012), surveys of 65 desktop and 94 mobile users). An earlier survey of 29 totally blind users found none of the three fully accessible ([ACM](https://dl.acm.org/doi/10.1145/3430263.3452433)).
- A blind user could tell a whiteboard was shared, but not what was written or erased ([PMC9483261](https://pmc.ncbi.nlm.nih.gov/articles/PMC9483261/)). Blind and low-vision developers describe extra "access labour" in software meetings ([NSF PAR](https://par.nsf.gov/servlets/purl/10544610)).
- The fallback is OCR, which users describe as ranging from very successful to yielding nothing useful ([WebAIM](https://webaim.org/blog/tips-for-accessible-screen-sharing/)). It loses headings and table structure ([imagemd](https://imagemd.org/2023/09/17/hacks-for-making-screenshots-screenshares-accessible/)).

**Intended user:** a blind student or engineer using NVDA on Windows (VoiceOver on macOS second) in classes, labs and standups where someone shares a spreadsheet, a code editor or slides.

## What it does

1. Open UnScreen in a second tab and press **Start** (Alt+Shift+S). Pick the meeting tab or window; your screen reader stays on UnScreen.
2. UnScreen says what is shared: *"Now showing: Spreadsheet, 'Q3 Pipeline', 12 rows, 6 columns."*
3. Read it like a web page: a `<table>` with column and row headers, a code listing with line numbers, or headings and lists.
4. When the presenter edits, you hear it once, politely: *"Acme Corp, Q3 revenue: $1.1M to $1.2M."* Your reading position does not move.
5. Ask what the presenter's pointer is on (Alt+Shift+P), step back through earlier versions, or type a question about the screen.

Anything UnScreen cannot read with confidence is shown as *unclear* or *unreadable* and announced as "possibly changed, unclear", never as a value.

## Results

<!-- bench:start -->
**Kill test (10 spreadsheets in a meeting window)**, 2026-10-21, reads by `gemini-3.6-flash`, no cross-check read (added after this run):

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sheet, meeting window, 720p, lossy | 6 of 10 | 99.1% | 41.3% | 0.9% | 49.8% | 100.0% | 79.6% |

Reconstruction time per frame: median 74.5 s, p95 106.9 s. Cost per frame: $0.0053.

**Without the model** (2026-10-21): with a scripted model answering instantly, an edit is spoken 2.7 s later (median of 5 edits, max 2.7 s). This is UnScreen's own share of the latency: capture, change gate, engine and announcement coalescing.

**Live loop** (sheet, 2026-10-21): no frame was read; the API returned rate-limit errors and timeouts (1 engine error). Nothing was announced.

OCR is Tesseract 5.5 (best of three settings) with help to find table cells; screen reader OCR gets none.
<!-- bench:end -->

Method, definitions and failures: [`/benchmark`](apps/web/src/routes/(site)/benchmark/+page.svelte) and [`bench/`](bench).

## Run it locally (about 10 minutes)

Requirements: Node 24 with pnpm, Python 3.12 with [uv](https://docs.astral.sh/uv/), Chrome or Edge, and a [Gemini API key](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/rahulgunwanistudy-2005/unscreen.git
```

```bash
cd unscreen && pnpm install && (cd services/engine && uv sync)
```

```bash
cp .env.example .env
```

Put your key in `.env` as `GEMINI_API_KEY=...`, then start the engine and the web app in two terminals:

```bash
pnpm dev:engine
```

```bash
pnpm dev:web
```

Open <http://localhost:5173/app>. With no meeting to hand, open <http://localhost:5173/fixture/sheet?seed=1> in another tab (a test spreadsheet that edits itself every 8 seconds), press Start and choose that tab.

### Checks

```bash
cd services/engine && uv run ruff check engine tests && uv run mypy engine && uv run pytest
```

```bash
cd apps/web && pnpm check && pnpm exec vitest run && pnpm exec playwright test
```

CI runs the same checks (`.github/workflows/ci.yml`) and never calls the live API: recorded model responses are replayed (`services/engine/tests/golden`).

### Benchmark

```bash
pnpm --filter @unscreen/bench capture
```

```bash
cd bench && PYTHONPATH=. uv run --project ../services/engine python -m unscreen_bench.degrade
```

```bash
cd bench && PYTHONPATH=. uv run --project ../services/engine python -m unscreen_bench.run --concurrency 1
```

`node bench/live-run.mjs` measures the live loop (engine on :8787, web on :5173).

## How we built it

```
Browser (SvelteKit, Svelte 5)                       Engine (FastAPI, Python 3.12)
getDisplayMedia ─▶ worker: dHash change gate ─WS─▶  pixel diff ─▶ full read  ┐
                   pointer tracker                               └▶ region read + verify ─▶ align ids ─▶ JSON patch
reader ◀─ in-place RFC 6902 patches ◀──────────WS── announcements ◀────────────────────────┘        Gemini API
```

Full diagram and reasoning: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Accessibility contract: [`docs/ACCESSIBILITY.md`](docs/ACCESSIBILITY.md). Every non-obvious call is logged with its reason in [`DECISIONS.md`](DECISIONS.md).

- **One contract.** The Pydantic document model generates the JSON Schema and the TypeScript types; CI fails if they drift.
- **Stable ids.** The model never mints ids. The aligner matches each new read to the previous version, so an edit becomes one `replace` on one text node and the screen reader's position survives. A Playwright test holds focus on a cell through 20 patches.
- **Two reads before a fact.** Every full read is checked by an independent second read with a different model; region re-reads are checked cell by cell on a 2× crop. Disagreements are marked unclear.
- **Change gate.** The browser sends a frame only when the screen changed and has been still for 300 ms, and recognises the presenter's pointer moving instead of sending it.

## Tools used

SvelteKit, Svelte 5, TypeScript, Python, FastAPI, Pydantic, Google Gemini API (`google-genai`), WebSockets, Web Workers, Screen Capture API, Playwright, axe-core, Vitest, pytest, Hypothesis, Tesseract (baseline only). Fonts: Atkinson Hyperlegible Next and Mono (Braille Institute), Doto.

## Limitations

- **Latency with the model is unproven.** UnScreen's own share is 2.7 s (median, scripted model). Measurements with Gemini were made on a free-tier key (20 requests per day per model), where refused calls were retried, so they show tens of seconds that are not the model's speed. See [`/benchmark`](apps/web/src/routes/(site)/benchmark/+page.svelte).
- Reading depends on Gemini; frames are sent to Google ([privacy](apps/web/src/routes/(site)/privacy/+page.svelte)). There is no offline mode.
- Tested on generated fixtures and Chrome on macOS. Manual NVDA results are in [`docs/research/results.md`](docs/research) only once sessions have happened.
- Pointer and Ask are tested with scripted model responses only, not yet against live Gemini.
- Screen capture needs a desktop browser; it does not work on phones.
- Digits damaged by video compression can be misread. The second read catches most, not all.

## Team

- Rahul Gunwani ([@rahulgunwanistudy-2005](https://github.com/rahulgunwanistudy-2005))

## Disclosure

- **Pre-existing work:** none. Created October 17–24, 2026.
- **AI assistance:** built with Claude Code as a coding assistant. At runtime, UnScreen uses Google Gemini to read shared screens.
- **Examples:** every spreadsheet, code file and slide shown is a generated test fixture from this repository.

## Licence

MIT
