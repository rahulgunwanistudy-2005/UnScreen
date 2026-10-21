# Accessibility

UnScreen is a screen-reader product first. This file is the contract the code is tested against, and the checklist for the manual NVDA and VoiceOver passes.

## Structure

- One `<h1>` per page. On the reader it is the shared content's title, so the first heading a user hits names what is being shared.
- Landmarks: `banner` (site header), `main` (controls, status, shared content), `complementary` (Changes, Pointer, Ask), `contentinfo` (footer). A "Skip to content" link is the first focusable element.
- Native elements only, with ARIA added only where HTML has no equivalent: a single `role="status"` region for announcements, a single `role="alert"` region used only for "Sharing ended" and "engine busy", and `aria-current` on the selected history version.

## Shared content

| Content | Markup |
| --- | --- |
| Spreadsheet | `<table>` with `<caption>` (title, row and column counts), `<th scope="col">` headers, and `<th scope="row">` on the first column when it names the rows (at least 80% of rows have a key). |
| Code | `<figure>` with a `<figcaption>` (file, language, line count) around a `<pre>`, one block per line, each starting with its line number. |
| Slides and documents | Headings (the slide's level 1 becomes `<h2>` under the page `<h1>`), paragraphs, and consecutive list items grouped into one `<ul>`. Figures are written as "Picture: …". |
| Unreadable value | The word "unreadable", never an empty cell. |
| Uncertain value | The reading followed by "(unclear)", with a wavy underline for sighted users. |

## Updates never move the reader

- Updates arrive as JSON-patch operations on stable ids and are applied in place. Rows and cells are keyed by id, so an edit changes one text node and an insert adds one row. No container is replaced.
- Tested: `apps/web/tests/focus.spec.ts` holds focus on a cell, applies 20 patches (edits, inserts and removals elsewhere, plus an edit to the focused cell itself), and checks that `document.activeElement` is the same element object throughout.
- Cells are `tabindex="-1"`: focusable when a user or NVDA moves focus there, but not 100 extra Tab stops. Focusing a cell tells the engine which row and column the user is on, so changes there are announced first.

## Announcements

- Polite only. Changes arriving within 1.5 s are spoken together, and nothing is spoken more often than once every 2 s.
- Order: a switch of content type first, then changes in the focused row or column, then everything else. After four items the rest is summarised as "N more changes in the Changes list".
- Verbosity: **all**; **important** (new content, rows or lines added or removed, scrolling); **quiet** (only where you are). Content switches and changes where you are always come through.
- Uncertain values are announced as "possibly changed, unclear", and unreadable ones as "now unreadable". A value is never spoken as fact unless two independent reads agreed.
- Numbers can be announced old-to-new ("$1.1M to $1.2M") or new only.

## Keyboard

- Every control is a native button, link or form field. Focus is always visible: a 3px ink outline with a 6px yellow halo.
- Shortcuts are Alt+Shift chords, matched on the physical key so macOS Option combinations work. The help page lists every shortcut, lets each be changed or turned off, and refuses chords that clash: bare letters (browse-mode quick keys), Ctrl+Alt+arrows (NVDA table navigation), and browser chords.

## Visual

- Contrast (WCAG 2.2): ink `#0F1E3D` on paper `#F3F5F7` and secondary text `#3A4766` on paper both exceed 7:1 (AAA). The dark theme is white on true black with the same yellow, the high-contrast scheme many low-vision readers already use.
- Body text is 18px (24px in large print), Atkinson Hyperlegible Next, from the Braille Institute.
- Works down to 360px wide; wide tables scroll inside their own region, never the page.
- Motion: one hero animation on the landing page, replaced by its final state with a play button when reduced motion is requested (system setting or the in-app switch).

## Manual test log

Manual passes with NVDA, VoiceOver and ChromeVox are recorded in `docs/research/results.md`, including what was found and fixed. Results are only written there after a pass has actually been done.
