# Verified facts

Fetched 2026-10-21. Where a fact differs from the build prompt, the docs win and the difference is noted in `DECISIONS.md`.

## Gemini API

Source: https://ai.google.dev/gemini-api/docs/models, /pricing, /rate-limits, /structured-output, /image-understanding, /media-resolution, /thinking, /migrate-to-interactions

- **SDK:** `google-genai` 2.31.0 on PyPI. `from google import genai; client = genai.Client()`. Async variant: `client.aio`.
- **Recommended API is now the Interactions API**: `client.interactions.create(model=..., input=[...], system_instruction=..., generation_config={...}, response_format=...)`. The migration guide says *"While `generateContent` remains fully supported, we recommend the Interactions API for all new development."* No shutdown date given.
- **Result text:** `interaction.output_text` (concatenated text added by the SDK). Usage: `interaction.usage.total_input_tokens`, `total_output_tokens`, `total_thought_tokens`, `total_tokens` (SDK type `Usage`).
- **Structured output:** `response_format` with `type: "text"`, `mime_type: "application/json"`, `schema: <JSON Schema>` (e.g. `Model.model_json_schema()`). Supported keywords: types incl. `null` via type arrays; `properties`, `required`, `additionalProperties`; string `enum`, `format`; number `enum`, `minimum`, `maximum`; array `items`, `prefixItems`, `minItems`, `maxItems`; `$ref` to `#`; `title`, `description`. `minLength`/`maxLength`/`minProperties`/`maxProperties` are silently stripped. Large or deeply nested schemas may be rejected (no numeric limit published). Validate on our side with Pydantic.
- **Image input:** item `{"type": "image", "mime_type": "image/webp", "data": <base64>, "resolution": "high"}`. WebP, PNG, JPEG, HEIC, HEIF supported. Inline request limit 20 MB total. Up to 3,600 images per request.
- **Image tokens (Gemini 3/4 `resolution` per item):** low 280, medium 560, high 1120 (= default `unspecified`), `ultra_high` 2240 (per-item only).
- **Bounding boxes:** documented convention is `box_2d = [ymin, xmin, ymax, xmax]` normalised to 0–1000.
- **Thinking:** `generation_config={"thinking_level": "low"}`. gemini-3.8-flash: low/medium/high (default medium). gemini-3.6-flash: minimal/low/medium/high. gemini-3.5-flash-lite: minimal/low/medium/high (default minimal). Thinking tokens billed at output rate.
- **Sampling params:** Gemini 4 and 3.6+ ignore `temperature`, `top_p`, `top_k` and return deprecation headers. Do not send them.
- **Models (stable):** `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-4-argon` (1M context). Preview: `gemini-3-flash-preview`, `gemini-3.1-pro-preview`. 2.5 family limited to previous users.
- **Pricing (USD / 1M tokens, paid tier):**
  - gemini-3.8-flash: input $0.75, output $3.75 through 2026-12-31 (then $1.50 / $7.50). Free tier available.
  - gemini-3.6-flash: same as 3.8-flash.
  - gemini-3.5-flash-lite: input $0.30, output $2.50. Free tier available.
  - gemini-3.1-flash-lite: input $0.25, output $1.50.
  - gemini-3.1-pro-preview: input $2.00, output $12.00 (≤200k). No free tier.
- **Rate limits:** not published per model any more; shown per project in AI Studio. Tier 1 spend limit $10 per 10 minutes. "Specified rate limits are not guaranteed."

## Chrome capture

Sources: https://developer.chrome.com/docs/web-platform/screen-sharing-controls, https://developer.mozilla.org/en-US/docs/Web/API/MediaStreamTrackProcessor, https://developer.mozilla.org/en-US/docs/Web/API/CaptureController

- `getDisplayMedia` options: `displaySurface` (`browser`/`window`/`monitor`, preselects a pane, Chrome 107), `monitorTypeSurfaces` (`include`/`exclude`, 119), `surfaceSwitching` (107), `selfBrowserSurface` (`exclude` default, 107), `systemAudio` (105). `preferCurrentTab: true` conflicts with `selfBrowserSurface: "exclude"`. Google recommends setting these explicitly.
- `CaptureController`: `new CaptureController()` passed as `controller` in options. `setFocusBehavior("no-focus-change")` keeps focus on the capturing page; called after `getDisplayMedia` resolves. Experimental, secure context only. Captured Surface Control adds `forwardWheel()` and zoom methods.
- `MediaStreamTrackProcessor`: limited availability, not Baseline. MDN: "Browsers differ on which global context they expose this interface in (e.g., only window in some browsers and only dedicated worker in others)." Standard form is worker-only and video-only; a track can be transferred to a worker with `postMessage({track}, [track])`.

## Screen readers and live regions

Sources: https://webaim.org/techniques/aria/, NVDA browse-mode docs (https://www.mintlify.com/nvaccess/nvda/features/browse-mode)

- Live regions must exist in the DOM at page load; "injecting it later doesn't work reliably". `polite` is read at the next pause; `assertive` interrupts and is for critical updates.
- NVDA browse mode reads a virtual buffer built from the DOM; the buffer updates on DOM changes. No current primary source documents caret behaviour under DOM mutation, so the product treats "never replace an ancestor of the reading position" as the rule and verifies it by test plus a manual NVDA pass (`docs/ACCESSIBILITY.md`).

## Not verified (could not find a primary source)

- A Chromium switch that auto-selects a tab by title for `getDisplayMedia` in automation. End-to-end tests therefore stub `getDisplayMedia` with a canvas stream fed by the fixture page (see `DECISIONS.md`).
