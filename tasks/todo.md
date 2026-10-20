## Task: UnScreen (Taskforge 2026)
## Goal: a deployed reader that turns any shared screen into a navigable, screen-reader-first document, with real benchmark numbers.

See PROGRESS.md for live status and DECISIONS.md for every non-obvious call. The full brief is the build prompt (§0–§13).

### Risks / open questions
- Gemini API key needed for the kill test (Day 1). CI replays recorded responses.
- NVDA caret behaviour under DOM mutation has no primary source; verified by focus-preservation test plus manual NVDA pass.
- Real blind participants may not be reachable in time; proxies must be labelled.
