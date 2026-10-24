# Design plan

Written in two design passes.

## Subject, audience, job

- **Subject:** a shared screen is a picture; UnScreen turns it into a document you can walk through. The user's world is NVDA's Speech Viewer, table navigation (Ctrl+Alt+arrows), braille cells, and high-contrast low-vision schemes.
- **Audience:** blind and low-vision students and engineers first; sighted judges and teammates second.
- **Primary job:** get someone from "someone is sharing" to reading the shared table in under a minute.

## Pass 1

- Colour: cool paper `#F3F5F7`, navy ink `#0F1E3D`, steel mosaic `#8FA3B8`, signal yellow `#FFC72C`, link blue `#1F4FE0`.
- Type: Atkinson Hyperlegible Next for everything, Atkinson Hyperlegible Mono for code and speech, a geometric grotesk for headlines.
- Layout: centred hero with the demo below, three cards for "how it works", a stats row with big numbers.

## Review against the brief and the skill's defaults

- A centred hero and three cards plus a big-number stats row is the SaaS-card kit and the "big number, small label" default. **Changed:** left-aligned single column; "how it works" is an ordered list because it really is a sequence; benchmark numbers sit in a real `<table>`, which is the product's own subject.
- A third, generic grotesk headline face adds nothing. **Changed:** the distinct display face is **Doto**, a dot-matrix face. Dots are both screen pixels and braille dots, so it carries the subject: it is used only for the wordmark and for the hero's "still a picture" state, never for text anyone must read. Every readable word is Atkinson Hyperlegible Next.
- Link blue as a fifth hue is decoration. **Dropped:** links are ink, underlined, thick underline on hover.
- Dark theme is black with yellow. That is close to the "near-black with one bright accent" tell, but here it is the subject's own convention: yellow on black is the classic high-contrast scheme many low-vision readers set system-wide. **Kept, justified:** true black `#000000`, not a tinted near-black, with paper-white text and yellow only for focus and change.

## Final tokens

| Token | Light | Dark | Role |
| --- | --- | --- | --- |
| `--paper` | `#F3F5F7` | `#000000` | page ground |
| `--ink` | `#0F1E3D` | `#F3F5F7` | text, table rules |
| `--ink-soft` | `#3A4766` | `#C9D1DE` | secondary text (AAA on paper in both) |
| `--mosaic` | `#8FA3B8` | `#3A4A5E` | unread pixel state, hero only |
| `--signal` | `#FFC72C` | `#FFC72C` | focus ring fill, changed cell, current history entry; never decoration |
| `--alarm` | `#A3141E` | `#FF8A8A` | share stopped, engine down |

- **Type scale** (1.25 ratio, 18px body for low vision): 14.4 / 18 / 22.5 / 28 / 35 / 44 / 55 px. Body line-height 1.55, headings 1.15. Measure ≤ 70ch.
- **Faces:** Atkinson Hyperlegible Next (400, 700, 800) body and headings; Atkinson Hyperlegible Mono (400, 700) code lines and the speech viewer; Doto (900) wordmark and hero mosaic only. All self-hosted (no request to a font CDN, matching the privacy promise).
- **Shape:** 2px radius on controls only; tables and sections have none. One border weight (2px ink) for structure, 1px `--ink-soft` at 35% for table rules.

## Layout

Landing, left aligned, single column, demo breaks out wider:

```
UnScreen (Doto)                         Help   Benchmark   Privacy
-----------------------------------------------------------------
Every screen share,
readable by a screen reader, live.            <- h1, 55px, 800
Zoom, Meet and Teams send shared content as a picture... (cite)
[ Start reading a shared screen ]   Try it on a test spreadsheet

+---------------------------------------------------------------+
| hero: dot mosaic of a real captured sheet  ->  live <table>    |
+---------------------------------------------------------------+
| Speech Viewer:  "Spreadsheet, 'Q3 Pipeline', 12 rows, ..."    |
+---------------------------------------------------------------+

How it works   (ol: 1 Share  2 Rebuild  3 Listen)
Measured, not claimed   (<table> of benchmark numbers vs OCR)
What leaves your computer   (one paragraph)
```

Reader (`/app`):

```
[banner] UnScreen | "Reading: Q3 Pipeline, version 12" | Start/Stop | Settings
[main]   h1 = shared title;  <table> / <pre> / headings, large type
[aside]  Changes (history timeline, newest first) | Pointer | Ask
         -> right column >= 1100px, below main otherwise
```

## Principles

1. The table is the product. The reader looks like a well-set document, not a dashboard.
2. Yellow means "here" or "this changed". Nothing else is yellow.
3. Dots mean "not read yet". Once text is read it is never shown in dots.
4. No cards. Sections are separated by space and real headings.
5. One motion moment: the hero mosaic resolving. Reduced motion shows the final table with a play button.
