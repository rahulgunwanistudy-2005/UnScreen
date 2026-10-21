# Session protocol

**Goal:** see whether a blind or low-vision participant can read and follow a shared spreadsheet faster, and with more trust, using UnScreen than using screen-reader OCR.

**Setup (facilitator)**
- Two Google accounts in one Meet. The presenter shares the `/fixture/sheet?seed=7&mode=static` tab. It's a scripted test sheet, so no real data is involved.
- The participant uses their own screen reader (NVDA preferred) and Chrome, with UnScreen open in a second tab.
- Read the consent form aloud and record the answers.

**Tasks (each done twice: A = NVDA OCR with NVDA+R, B = UnScreen; order alternates between participants)**
1. **Find a value:** "What is [row key]'s [column]?"
2. **What changed:** the presenter edits one cell. "What changed?" (Up to 60 seconds.)
3. **Pointer:** the presenter rests the mouse on a cell. "What is my pointer on?"

**Measures per task:** success (yes / partly / no), time in seconds from question to answer, trust rating 1–5 ("How sure are you that your answer is right?"), and a note on what happened.

**Closing questions**
1. What was hardest?
2. Would you use this in a real class or meeting? What would stop you?
3. Anything it said that you didn't believe?

**Afterwards:** write results into `results.md` the same day, with participant ids P1–P3 only. If no blind or low-vision participant could be reached by Friday 18:00 IST, run three sighted proxies with the screen off and NVDA on, and label them *proxy* everywhere.
