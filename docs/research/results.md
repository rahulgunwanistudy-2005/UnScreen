# Human validation results

Status updated 2026-10-24. No human session has been recorded. Automated focus and axe checks are not a screen-reader pass or a participant study. No participant, quote, trust rating or completion time is claimed.

## Publishable summary

No human screen-reader pass or participant session has been recorded. NVDA, VoiceOver and real-meeting validation remain pending. Automated browser checks cover focus preservation and accessibility rules; they do not establish usability with a screen reader.

## Manual screen-reader pass — ready to run, not completed

The prepared validation build is at http://localhost:5174/app with its engine on port 8790. A normal development setup uses http://localhost:5173/app and engine port 8787. Choose Watch a recorded session for a zero-model-call rehearsal; use Start for the actual Meet test. On Windows use NVDA with Chrome; on macOS use VoiceOver with Chrome. Record the exact OS, browser and screen-reader versions, date, operator and whether the content came from a real Google Meet or the fixture canvas harness.

| Check | Action and expected behavior | Outcome / finding |
| --- | --- | --- |
| Start and capture | Start, choose a tab. Focus stays in UnScreen; first content is announced. | Pending |
| Table headers | Navigate with NVDA Ctrl+Alt+arrows or VoiceOver table interaction. Both row and column headers identify values. | Pending |
| Position during edits | Stay on a cell while another changes. One polite announcement; reading position remains. | Pending |
| Unclear values | Read a flagged value and trigger an unclear edit. It says unclear and does not state the guessed new value. | Pending |
| Code and slides | Read line numbers, indentation, headings and lists. Switch content type. | Pending |
| Shortcuts | Exercise every shortcut in Help, remap one, disable shortcuts and restore it. | Pending |
| Changes | Open an earlier version and return to the latest version. | Pending |
| Ask | Ask a visible-content question and follow a cited reference. Try an unanswerable question. | Pending |
| Pointer | Move the presenter pointer, request its target and follow the target link. | Pending |
| Share stopped | Stop sharing from Chrome. The stopped message is announced and last content remains. | Pending |
| Engine down | Stop the engine. Reconnection status is readable; last content remains. Restart it. | Pending |
| Daily limit | Use a separate test engine with zero model-call allowance. A daily-limit message appears. | Pending |
| Hear it | Keep screen-reader mode checked. Speech preview stays off and does not overlap the reader. | Pending |

## Participant sessions — not completed

Follow `protocol.md` and `consent.md`. Obtain consent before starting. Label a sighted participant with the screen off as **sighted proxy** everywhere; do not describe that as a blind-user session. Alternate OCR / UnScreen order. No outreach has been sent by this session.

Copy one row per task only after observing it:

| Participant ID | Blind/low-vision participant or sighted proxy | Tool / order | Task | Success (yes/partly/no) | Seconds measured | Trust rating | Finding / fix |
| --- | --- | --- | --- | --- | --- | --- | --- |

Record consent privately. Publish a quote only after obtaining written permission for that exact wording. Keep personal contacts out of this repository.
