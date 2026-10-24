# Demo recording plan — under two minutes

Status: ready to record locally; no actual video or upload exists. Hosting is excluded by the user. A recording of a local build must be labelled local. Do not imply that the screen reader, real meeting or human study has been tested before it has.

The local build includes a genuine recorded-session demo for rehearsal without more model calls. The final human demonstration should still show the actual screen reader and state whether it is using a recording or a live share.

Use Chrome with NVDA on Windows, or VoiceOver on macOS and identify which. Keep Hear it disabled when using a screen reader. NVDA Speech Viewer or VoiceOver's caption panel can help transcribe actual output. Show only owned generated fixture content, with no API keys or personal data.

| Target time | Shot | Audio and caption plan |
| --- | --- | --- |
| 00:00–00:15 | Shared fixture inside a meeting, or a clearly labelled fixture tab if the real meeting has not happened | Explain the picture-only barrier. Do not invent a screen-reader utterance. |
| 00:15–00:40 | Start UnScreen and choose the tab. Navigate headers and values | Keep actual NVDA/VoiceOver speech audible and transcribe it verbatim. |
| 00:40–01:00 | Edit one value while focus remains on another | Capture the real announcement and focus behavior. Keep uncertainty warnings and failures. |
| 01:00–01:20 | Switch to code; pointer and Ask | Show actual results. A failed question is a limitation, not a reason to dub a successful answer. |
| 01:20–01:40 | Current benchmark page | Cite only the displayed measured result, its date and configuration. |
| 01:40–01:55 | Privacy, pending validation and local setup | State the actual validation status. Use a public URL only after the user separately publishes it. |

`docs/video/narration-draft.md` and `captions-draft.vtt` are drafts. After recording, make a verbatim `transcript.md`, retime a final `captions.vtt`, check the complete video is under two minutes and verify captions are legible. A written script is not a finished video.

No participant quote may be included without written permission for that exact wording. Do not call sighted proxies blind participants. Upload/submission and public-link checks remain pending; no URL is invented in the Devpost draft.
