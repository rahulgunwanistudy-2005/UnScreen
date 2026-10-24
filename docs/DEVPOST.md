# Devpost submission draft

Local submission draft. Results are generated from `bench/results`. No project publication or submission has occurred. Paid-tier fixture benchmarks are now measured. Real Google Meet validation, human sessions and the actual video remain pending; do not present this draft as a completed user study.

**Tagline:** Every screen share, readable by a screen reader, live.

## Inspiration

In a class or a standup, someone says "as you can see on my screen". Zoom, Google Meet and Microsoft Teams send that screen as a picture, so a screen reader can only say that someone is sharing. A study of 65 desktop and 94 mobile screen reader users found all three tools render shared content as an image (Leporini, Buzzi and Hersh, ACM TACCESS 2023). The fallback is OCR, which one screen reader user on WebAIM described as ranging from very successful to yielding nothing useful. Even when OCR works, it reads flat lines: a spreadsheet loses its rows and columns, and nobody tells you when a number changes.

## Intended user and the barrier

**User:** a blind student or engineer using NVDA on Windows (VoiceOver on macOS second) in classes, labs and standups where someone shares a spreadsheet, a code editor or slides.

**Barrier:** shared screens are images. The user cannot read the table being discussed, cannot tell what the presenter just changed, and cannot follow "this cell here". They either ask someone to read it out or fall back to OCR that loses structure.

## What it does

UnScreen runs in a second browser tab. Press Start, pick the meeting tab or window, and your screen reader stays on UnScreen.

- It says what is shared: "Now showing: Spreadsheet, 'Q3 Pipeline', 12 rows, 6 columns."
- It rebuilds the screen as a real `<table>` with row and column headers, a code listing with line numbers, or headings and lists. NVDA table navigation (Ctrl+Alt+arrows) works.
- When the presenter edits, you hear it once, politely: "Acme Corp, Q3 revenue: $1.1M to $1.2M." Your reading position does not move.
- Anything it cannot read with confidence is marked unclear and announced as "possibly changed, unclear", never as a value.
- Alt+Shift+P says what the presenter's pointer is on. A Changes list lets you read any earlier version. You can type a question about the screen, and the answer cites the cells it used.
- It needs nothing from the presenter and works with any meeting app.

## How we built it

Architecture image: `docs/gallery/architecture.png`; accessible SVG: `docs/gallery/architecture.svg`.

- **Browser (SvelteKit, Svelte 5, TypeScript):** `getDisplayMedia` with `CaptureController` so focus stays on UnScreen. A worker hashes a 320×180 grayscale grid per tile and sends a frame only when the screen changed and has been still for 300 ms. It recognises the presenter's pointer moving instead of sending it.
- **Engine (Python, FastAPI, Pydantic):** compares each frame with the last, then chooses a full read or a region re-read of just the changed cells. Each read goes to Google Gemini with a strict JSON schema. Every full read is checked by an independent second read with a different model, and every changed cell by a 2× crop read. Disagreements become "unclear".
- **Stable ids:** the aligner matches each read to the previous version and keeps ids, so an edit becomes one JSON-patch `replace` on one text node. The browser applies patches in place, and the screen reader's position survives. A Playwright test holds focus on a cell through 20 patches.
- **One contract:** the Pydantic model generates the JSON Schema and TypeScript types; CI fails on drift. CI replays recorded Gemini responses and never calls the live API.

## Tools used

SvelteKit, Svelte 5, TypeScript, Python, FastAPI, Pydantic, Google Gemini API (`google-genai`, models `gemini-3.6-flash` and `gemini-3.5-flash-lite`), WebSockets, Web Workers, Screen Capture API, Playwright, axe-core, Lighthouse, Vitest, pytest, Hypothesis, Tesseract (baseline only). Fonts: Atkinson Hyperlegible Next and Mono from the Braille Institute.

**Built with:** svelte, sveltekit, typescript, python, fastapi, pydantic, gemini-api, google-genai, websockets, web-workers, playwright, axe-core, vitest, pytest

## Results (benchmark and user sessions)

<!-- bench:start -->
**Configuration comparison: gemini-3.6-flash / gemini-3.5-flash-lite**, 2026-10-24, reads by `gemini-3.6-flash`, cross-checked by `gemini-3.5-flash-lite`:

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) | Marked unclear/unreadable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sheet, meeting window, 720p, lossy | 10 of 10 | 99.6% | 41.3% | 0.4% | 49.8% | 100.0% | 79.6% | 4 of 775 |

Reconstruction time per frame: median 11.3 s, p95 12.0 s. Cost per frame: $0.0094.

**Configuration comparison: gemini-3.6-flash / groq:qwen/qwen3.8-27b**, 2026-10-24, reads by `gemini-3.6-flash`, cross-checked by `groq:qwen/qwen3.8-27b`:

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) | Marked unclear/unreadable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sheet, meeting window, 720p, lossy | 1 of 1 | 100.0% | 5.3% | n/a | 77.8% | 100.0% | 80.0% | 75 of 75 |

Reconstruction time per frame: median 7.0 s, p95 7.0 s. Cost per frame: $0.0074.

**Configuration comparison: mistral:mistral-small-2603 / gemini-3.5-flash-lite**, 2026-10-24, reads by `mistral:mistral-small-2603`, cross-checked by `gemini-3.5-flash-lite`:

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) | Marked unclear/unreadable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sheet, meeting window, 720p, lossy | 0 of 1 | n/a | 5.3% | n/a | 77.8% | n/a | 80.0% | 0 of 0 |

Latency: not measured.

**Focused code and slide benchmark**, 2026-10-24, reads by `gemini-3.6-flash`, cross-checked by `gemini-3.5-flash-lite`:

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) | Marked unclear/unreadable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code, meeting window, 720p, lossy | 10 of 10 | 85.1% | 7.5% | 9.2% | 96.1% | 100.0% | 88.0% | 35 of 295 |
| slide, meeting window, 720p, lossy | 10 of 10 | 62.8% | 48.7% | 7.5% | 53.7% | 100.0% | 100.0% | 29 of 78 |

Reconstruction time per frame: median 11.1 s, p95 13.6 s. Cost per frame: $0.0094.

**Historical kill test (10 spreadsheets in a meeting window)**, 2026-10-21, reads by `gemini-3.6-flash`, no cross-check read (added after this run):

| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) | Marked unclear/unreadable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sheet, meeting window, 720p, lossy | 6 of 10 | 99.1% | 41.3% | 0.9% | 49.8% | 100.0% | 79.6% | 0 of 459 |

Reconstruction time per frame: median 74.5 s, p95 106.9 s. Cost per frame: $0.0053.

**Same 10 frames, one model each** (spreadsheets in a meeting window, no cross-check):

| Model | Read | Exact | Wrong as fact | Right place | Median time per frame | Not read because |
| --- | --- | --- | --- | --- | --- | --- |
| `groq:qwen/qwen3.8-27b` | 3 of 10 | 60.9% | 1.5% | 100.0% | 54.5 s | output cut off by the free-tier token limit (7) |
| `gemini-3.6-flash` | 6 of 10 | 99.1% | 0.9% | 100.0% | 74.5 s | timeout or connection error (4) |

**Without the model** (2026-10-21): with a scripted model answering instantly, an edit is spoken 2.6 s later (median of 5 edits, max 2.6 s). This is UnScreen's own share of the latency: capture, change gate, engine and announcement coalescing.

**Live loop** (sheet, 2026-10-21): no frame was read; the API returned rate-limit errors and timeouts (1 engine error). Nothing was announced.

**Live loop** (code, 2026-10-24): 6 scripted changes, recall 100.0%, precision 54.5%, change to announcement median 11.2 s.

**Live loop** (sheet, 2026-10-24): 11 scripted changes, recall 100.0%, precision 100.0%, change to announcement median 8.5 s, final table 42 of 42 cells correct.

**Live loop** (sheet, 2026-10-24): 13 scripted changes, recall 100.0%, precision 86.7%, change to announcement median 8.7 s, final table 42 of 42 cells correct.

OCR is Tesseract 5.5 (best of three settings) with help to find table cells; screen reader OCR gets none.
<!-- bench:end -->

**Human validation:** No human screen-reader or participant session has been recorded. See `docs/research/results.md`. Automated checks do not replace that pass.

## Challenges

- **Keeping a screen reader's place while the page changes.** Replacing a table makes NVDA lose its position, so updates had to be surgical: stable ids minted once, id-aware JSON patches, and in-place application. We wrote a test that holds focus through 20 patches and checked that it fails when the view is rebuilt.
- **Never stating a guess as fact.** One meeting-codec frame had four digits misread with full confidence (6 for 8, 9 for 3). We added an independent second read; disagreements are marked unclear. It flags disagreements, but agreeing reads can still share an error.
- **Choosing a model.** UnScreen can use Gemini, Groq or Mistral through one interface. On the same 10 frames, Groq's Qwen 3.8 generated a read in about 1.5 seconds, but on the free tier 7 of 10 reads were cut off by its 1,000-token-per-minute output limit, and the 3 it finished averaged 60.9% exact, against Gemini's 99.1%. The historical Mistral attempt had a zero-request quota. The owner now confirms an active plan; model listing succeeds, but the new generation screening still returned a provider rate limit. Mistral is excluded from the selected configuration.
- **The free tier.** Our Gemini key allowed 20 requests per day per model. We first misread the resulting 429 retries as slow models, until we read the quota in the error body.

## Accomplishments

- A complete loop from screen capture to a navigable, announced document, tested end to end in a real browser.
- A measured paid-tier spreadsheet configuration, plus separate code/slide results and live-loop evidence. Exactness, wrong-as-fact rates and failures come from the generated tables above.
- Automated focus preservation, recording playback and accessibility-rule checks pass. Human screen-reader validation remains pending.

## Limitations

- **Paid-tier latency is now measured on generated fixtures.** Current and historical runs are labelled in the generated results above. It is not yet a real Google Meet or human screen-reader measurement, and the model can still state an incorrect value with confidence.
- Current code and slide/document measurements are shown above. Their accuracy is substantially lower than the spreadsheet result; indentation and block segmentation matter. The smaller single-variant benchmark was run to minimize spending; the full multi-resolution benchmark was cut.
- Pointer and Ask have been exercised against live Gemini. The first loop found a cursor-direction bug; that failure is retained and follow-up checks are documented.
- Frames are sent to the configured provider. The default local engine uses paid Gemini billing, confirmed by the owner; Gemini Interactions storage is disabled. The historical free-tier results do not establish paid-tier performance. Optional Mistral and Groq configurations require their own privacy disclosure.
- Tested in Chrome on macOS. Tab capture needs a desktop browser.
- No human screen-reader pass or participant/proxy session has been recorded. A real Google Meet test and demo recording are also pending. Current evidence covers generated fixtures and automated browser checks.

## What we learned

- For screen reader users, *where you are* matters as much as *what it says*: a correct update that moves the reading position is a regression.
- "Uncertain" has to be a first-class value all the way from the model's schema to the spoken sentence.
- Read the error body. Our "slow API" was a daily quota.

## What's next

- Extend the measured single-variant benchmark to all resolutions when the budget permits, and validate the actual Google Meet and screen-reader workflow.
- Sessions with blind participants through the BITS Pilani disability support office and NAB India.
- On-device reading with Chrome's built-in Prompt API where available, for privacy and speed.
- Large-print reflow for low-vision users, and an accessible handout export of a whole session.

## Build instructions

Live: https://unscreen-igkn.onrender.com (engine health: https://unscreen-engine.onrender.com/healthz). Source: https://github.com/rahulgunwanistudy-2005/UnScreen . See `README.md` for local setup and `render.yaml` for the hosted configuration.

## Team

- Rahul Gunwani (from the existing project credits; no additional teammates supplied).

## Pre-existing work

None. Created October 17–24, 2026.

## Runtime model

At runtime, UnScreen uses Google Gemini to read shared screens.

## Permissions

All examples shown are generated test fixtures from this repository; no real meeting content or personal data is shown.

## Video and public links

Actual video: pending user recording with NVDA or VoiceOver. The recording plan and draft captions are in `docs/VIDEO.md` and `docs/video/`. No video URL or submitted Devpost page is claimed yet. Hosted reader: https://unscreen-igkn.onrender.com

## Gallery (local previews, not deployed screenshots)

- `docs/gallery/home-local.png` — Alt: "UnScreen home page with a shared-spreadsheet hero and measured historical benchmark results."
- `docs/gallery/reader-recording-local.png` — Alt: "The real UnScreen reader playing a recorded Gemini spreadsheet session, with an explicit recording label, native table and Changes history. This is a recording of generated test content, not a live meeting."
- `docs/gallery/benchmark-local.png` — Alt: "Local benchmark page with historical model results, failures and an explicit pending human-validation status."
- `docs/gallery/help-local.png` — Alt: "Keyboard help and shortcut remapping on the local UnScreen site."
- `docs/gallery/privacy-local.png` — Alt: "Local privacy page explaining provider access, in-memory frames and daily spending accounting."
- `docs/gallery/architecture.png` — Alt: "Browser capture sends changed frames through a daily allowance guard and independent vision reads, then stable identifiers preserve the reader while verified changes are announced."
