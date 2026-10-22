# Devpost submission draft

Draft for review. Every number comes from `bench/results` (see `/benchmark`). Fill in or remove anything in [brackets] before submitting. Re-run `pnpm bench:publish` and update the numbers if the full benchmark runs on a paid key.

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

[Attach `docs/ARCHITECTURE.md` diagram as an image.]

- **Browser (SvelteKit, Svelte 5, TypeScript):** `getDisplayMedia` with `CaptureController` so focus stays on UnScreen. A worker hashes a 320×180 grayscale grid per tile and sends a frame only when the screen changed and has been still for 300 ms. It recognises the presenter's pointer moving instead of sending it.
- **Engine (Python, FastAPI, Pydantic):** compares each frame with the last, then chooses a full read or a region re-read of just the changed cells. Each read goes to Google Gemini with a strict JSON schema. Every full read is checked by an independent second read with a different model, and every changed cell by a 2× crop read. Disagreements become "unclear".
- **Stable ids:** the aligner matches each read to the previous version and keeps ids, so an edit becomes one JSON-patch `replace` on one text node. The browser applies patches in place, and the screen reader's position survives. A Playwright test holds focus on a cell through 20 patches.
- **One contract:** the Pydantic model generates the JSON Schema and TypeScript types; CI fails on drift. CI replays recorded Gemini responses and never calls the live API.

## Tools used

SvelteKit, Svelte 5, TypeScript, Python, FastAPI, Pydantic, Google Gemini API (`google-genai`, models `gemini-3.6-flash` and `gemini-3.5-flash-lite`), WebSockets, Web Workers, Screen Capture API, Playwright, axe-core, Lighthouse, Vitest, pytest, Hypothesis, Tesseract (baseline only). Fonts: Atkinson Hyperlegible Next and Mono from the Braille Institute.

**Built with:** svelte, sveltekit, typescript, python, fastapi, pydantic, gemini-api, google-genai, websockets, web-workers, playwright, axe-core, vitest, pytest

## Results (benchmark and user sessions)

**Reading accuracy** (kill test: 10 spreadsheets shared inside a meeting window, downscaled to 720p and JPEG-compressed; 6 read before the free-tier quota ran out):

| | UnScreen | Tesseract OCR (best of 3 settings, helped to find cells) |
| --- | --- | --- |
| Cells read exactly | 99.1% | 41.3% |
| Wrong but stated as fact | 0.9% | 49.8% |
| Found values in the right row and column | 100% | 79.6% |

**UnScreen's own latency:** with a scripted model that answers instantly, an edit is spoken 2.6–2.7 s later (median of 5 edits, in each of two runs). Latency with Gemini could not be measured fairly; see Limitations.

**Accessibility checks:** axe-core reports zero violations on every page in light and dark themes. Lighthouse accessibility scores 100 on all five pages.

**User sessions:** [Fill from `docs/research/results.md`. If no blind participant took part, say so plainly; label proxy sessions as proxies.]

## Challenges

- **Keeping a screen reader's place while the page changes.** Replacing a table makes NVDA lose its position, so updates had to be surgical: stable ids minted once, id-aware JSON patches, and in-place application. We wrote a test that holds focus through 20 patches and checked that it fails when the view is rebuilt.
- **Never stating a guess as fact.** One meeting-codec frame had four digits misread with full confidence (6 for 8, 9 for 3). We added an independent second read; disagreements are marked unclear. It catches most such cells, not all.
- **Choosing a model.** UnScreen can use Gemini, Groq or Mistral through one interface. On the same 10 frames, Groq's Qwen 3.8 generated a read in about 1.5 seconds, but on the free tier 7 of 10 reads were cut off by its 1,000-token-per-minute output limit, and the 3 it finished averaged 60.9% exact, against Gemini's 99.1%. Mistral could not be tested: the key's workspace had a limit of zero requests.
- **The free tier.** Our Gemini key allowed 20 requests per day per model. We first misread the resulting 429 retries as slow models, until we read the quota in the error body.

## Accomplishments

- A complete loop from screen capture to a navigable, announced document, tested end to end in a real browser.
- 99.1% of cells read exactly on degraded meeting frames, against 41.3% for a generously helped OCR baseline, with every number generated from result files.
- An accessibility contract that is tested, not asserted: focus preservation, zero axe violations, Lighthouse 100.

## Limitations

- **Latency with the model is unproven.** UnScreen's own share is 2.6–2.7 s. Measurements with Gemini ran on a free-tier key (20 requests per day per model) and include waiting after refused requests, so they show tens of seconds that do not reflect the model's speed.
- The benchmark covers 6 spreadsheet frames. Code and slides are built and unit-tested, but their accuracy was not benchmarked because of the quota.
- Pointer and Ask work end to end with scripted model responses in tests; they have not yet been tried against live Gemini.
- Frames are sent to Google's Gemini API. On the free tier, Google may use them to improve products and humans may review them. Do not use UnScreen for confidential meetings on a free key.
- Tested in Chrome on macOS. Tab capture needs a desktop browser.
- [User testing status.]

## What we learned

- For screen reader users, *where you are* matters as much as *what it says*: a correct update that moves the reading position is a regression.
- "Uncertain" has to be a first-class value all the way from the model's schema to the spoken sentence.
- Read the error body. Our "slow API" was a daily quota.

## What's next

- Run the full 120-frame benchmark (code, slides, all resolutions) and the live-loop measurement on a paid key.
- Sessions with blind participants through the BITS Pilani disability support office and NAB India.
- On-device reading with Chrome's built-in Prompt API where available, for privacy and speed.
- Large-print reflow for low-vision users, and an accessible handout export of a whole session.

## Build instructions

See the README: [repository link]. Local setup takes about 10 minutes.

## Team

- Rahul Gunwani [confirm name and add any teammates]

## Pre-existing work

None. Created October 17–24, 2026.

## AI assistance disclosure

Built with Claude Code as a coding assistant. At runtime, UnScreen uses Google Gemini to read shared screens.

## Permissions

All examples shown are generated test fixtures from this repository; no real meeting content or personal data is shown.

## Gallery (alt text drafted)

1. Landing page. Alt: "UnScreen home page. Headline: Every screen share, readable by a screen reader, live. Below, a real meeting frame of a spreadsheet resolving from dots into a table."
2. Reader with a spreadsheet. Alt: "The reader showing a rebuilt spreadsheet as a table with headers, a status line, and the Changes list on the right."
3. Benchmark page. Alt: "Benchmark table comparing UnScreen and OCR: 99.1% against 41.3% of cells read exactly."
4. Architecture diagram. Alt: "Diagram: browser capture and change gate send frames over a WebSocket to the engine, which reads with Gemini, aligns ids and sends back patches and announcements."
