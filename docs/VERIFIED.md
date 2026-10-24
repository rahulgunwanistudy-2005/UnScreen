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

## Groq and Mistral (fetched 2026-10-22)

Sources: https://console.groq.com/docs/vision, /docs/structured-outputs, /docs/model/qwen/qwen3.8-27b; Mistral OpenAPI spec (https://docs.mistral.ai/openapi.yaml) and https://docs.mistral.ai/capabilities/vision/

- **Groq vision models:** `qwen/qwen3.8-27b` (the only one this key lists) and `meta-models/muse-spark-open` (limited preview). Qwen: 3 images per request, each counted as 2,048 input tokens, 20 MB max; 131,072-token context, 16,384 max output; reasoning by default, turned off with `reasoning_effort: "none"`. Price: $0.80 input, $4.00 output per 1M tokens.
- **Groq structured output:** `response_format: {type: "json_schema", json_schema: {name, schema, strict: true}}` on `qwen/qwen3.8-27b` and others. Strict mode needs every property required and `additionalProperties: false`.
- **Groq free tier, as observed:** output-tokens-per-minute limit of 1,000 for this model (from a 429 body); a request whose `max_completion_tokens` exceeds it is refused outright.
- **Mistral vision models listed for this key:** `mistral-medium-latest` (Medium 3.5), `mistral-small-latest` (2603), `ministral-{3b,8b,14b}-latest`, `magistral-{small,medium}-latest`, `mistral-ocr-latest`.
- **Mistral request shape:** image chunk `{"type": "image_url", "image_url": "data:…"}` (string or `{url}`); `response_format` `{type: "json_schema", json_schema: {name, schema, strict}}`.
- **Mistral key status, as observed:** every call returns 429 with `x-ratelimit-limit-req-minute: 0`, meaning the workspace has no active plan. Mistral publishes no per-model API prices on its pricing page; none are assumed.

## Rechecked 2026-10-24

- User reports Gemini billing and Mistral plan active. Model listing returned HTTP 200 for all three provider keys. This does not prove generation quotas; no paid generation was attempted before a spending cap was agreed.
- Gemini Interactions stores requests by default. `store=false` opts into stateless behavior; added to every request. Source: https://ai.google.dev/gemini-api/docs/interactions-overview#data-storage-and-retention . Paid-tier training and abuse-monitoring terms still apply.
- Gemini 3.6 Flash standard paid rates remain $0.75 input / $3.75 output per million tokens through 2026-12-31. Source: https://ai.google.dev/gemini-api/docs/pricing .
- Mistral Medium 3.5 model card lists $1.50 input / $7.50 output per million tokens: https://docs.mistral.ai/models/mistral-medium-3-5-26-04 . Mistral Small 4 (`mistral-small-2603`) lists $0.15 input / $0.60 output: https://docs.mistral.ai/models/mistral-small-4-0-26-03 . Prices now recorded in `cost.py`; aliases must be rechecked when providers move them.
- Firecrawl retrieval was unavailable because the connected account has no credits; official documentation was read using the available web tool instead.

## Live access verified in the completion pass

Gemini generation succeeded on the active paid key. The dated configuration, focused content and live-loop JSON files in `bench/results` contain actual outcomes and token usage. The fresh focused benchmark recorded zero replayed calls.

The Mistral Small screening returned HTTP 429 with a provider rate-limit message despite the user's active plan; it was not retried. This does not establish the account's plan status. The Groq cross-check screening returned a result that left every primary value unclear, so it was excluded from production. Gemini remains the shipped default.

The chosen configuration and exact metrics are referenced by `bench/results/production.json`; do not substitute old free-tier measurements for the new paid-tier evidence. Code and slide/document performance is weaker and is reported separately.
