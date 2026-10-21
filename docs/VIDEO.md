# Demo video script (2:00 or less)

Record on Windows with NVDA speech audible, or on macOS with VoiceOver. Turn on NVDA's Speech Viewer so its text can be captioned. Use a paid-tier Gemini key so the reads come back promptly; on the free tier the demo will stall after 20 requests. Show only fixture content. Add captions, and publish this script alongside as the transcript.

| Time | Picture | Sound and captions |
| --- | --- | --- |
| 0:00–0:15 | A meeting tab (Meet, or the generic meeting fixture `/fixture/sheet?seed=3&frame=meet`) with a spreadsheet shared. Speech Viewer open. | NVDA reads the meeting page: it can only say that someone is presenting. Caption: "This is all a screen reader gets from a shared screen." |
| 0:15–0:45 | Switch to UnScreen. Press Alt+Shift+S, pick the meeting tab. The table appears. Move with Ctrl+Alt+arrows. | NVDA: "Now showing: Spreadsheet …", then the headers and values as you move. Caption the key lines. |
| 0:45–1:05 | The presenter edits a cell. Keep focus on a different row. | The polite announcement ("Row, column: old to new"). Show that the focus stayed on the same cell. |
| 1:05–1:20 | The presenter switches to the code fixture. Press Alt+Shift+P. | "Now showing: Code …", line numbers, then "Pointer is on line N …". |
| 1:20–1:40 | The `/benchmark` page. | Voice-over: "On compressed meeting frames, UnScreen read 99.1% of cells exactly; OCR, given help, read 41.3%. And only 0.9% of what it stated was wrong." Use the numbers on the page at recording time. |
| 1:40–2:00 | Limitations and the URL. | "It needs a paid model key to be fast, and it has been tested on fixtures, [with N blind participants / with sighted proxies]. Try it at [URL]." Add a participant quote only with written permission. |

Do not show a value being announced that UnScreen marked unclear. If one occurs, keep it and let it say "possibly changed, unclear"; that is the product working.
