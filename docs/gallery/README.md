# Local gallery

These are local previews, not screenshots of a deployed service or a real Google Meet. `reader-recording-local.png` shows the real `/app` reader playing actual server messages from the successful paid Gemini spreadsheet loop. The app labels it a recording and disables live Ask/pointer requests during playback. Source: `bench/results/2026-10-24-live-paid-sheet-fixed.json` and `apps/web/static/recordings/session.json`. Capturing it makes no model API calls.

Alt text and gallery order are in `docs/DEVPOST.md`. `architecture.svg` includes a title and description, and `architecture.png` is its raster export. Do not relabel these as deployment, human-validation or live-meeting evidence.

Regenerate with Python Playwright and `bench/gallery.py --base http://localhost:5174`. Use `--browser` only when selecting an installed Chromium executable. The optional `--document` argument renders a historical golden document in the test harness instead; the final gallery uses the genuine recording in the real reader.
