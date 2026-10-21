# Critique pass

Screenshots of every page at 1440 px and 390 px, in light and dark, are in `docs/design/critique/` (taken 2026-10-22 with reduced motion, so the hero shows its final state).

| Page | Found | Changed |
| --- | --- | --- |
| Home | The hero frame kept the source image's aspect ratio, leaving an empty band under the finished table. | The stage takes the table's height once the animation ends. |
| Home | Hero dots were too faint on light paper; the one bold element read as noise. | Dots drawn in ink, with size following darkness. |
| Home | Mid-animation cells blended text into the yellow flash (Lighthouse contrast failure). | Cells appear at full contrast; the flash is an inset outline. |
| All | The footer's top rule doubled the header rule and edged towards the hairline-broadsheet look. | **Accessory removed:** footer rule. |
| Benchmark | At 390 px the live-loop table pushed the whole page sideways (1000 px wide). | Both tables sit in focusable scroll regions. |
| Help | At 390 px the shortcuts table overflowed by 20 px. | Scroll region and tighter buttons; no page overflows at 360 or 390 px. |

Checked against the skill's tells: no cream and terracotta, no single acid accent on near-black (the dark theme is true black with yellow, justified in `PLAN.md`), no card grid, no all-caps eyebrows, no middle-dot meta strings, no arrows on buttons, one motion moment only.
