# Real Google Meet fixture group — pending capture

No real meeting frames have been captured in this session. The generated `meet1080p` fixtures are simulated meeting chrome, not Google Meet evidence.

With the user's participation and consent, join one Google Meet with two owned accounts/devices. Present a Google Sheet owned by the user, then capture at least six distinct receiving-side frames. Include changes, small text, meeting chrome and captions if enabled. Keep participant faces, names, chat and unrelated tabs out of the capture; use only the agreed test content. Nothing is captured automatically by creating this folder.

Save each approved screenshot here as `meet-01.png` and pair it with `meet-01.truth.json` containing the visible sheet's exact headers and rows in the fixture truth format. Hand-check values against the source sheet. Unknown content must not be invented as truth.

Create `manifest.json` only after capture, with entries containing `id` (for example `meet-01`), `file` (the screenshot filename), `kind` (`sheet`), `variant` (`real-meet`), and the actual pixel `width` and `height`. Add a separate consent/provenance note without personal contacts. Do not put example rows into the benchmark manifest before capture.

From `bench/`, run the existing benchmark with `--frames-dir fixtures/real --kinds sheet --variants real-meet --concurrency 2 --name real-meet`, using the selected model configuration and the shared spending ledger. Then run `pnpm bench:publish`. The group's name must remain `real-meet`, distinct from generated meeting-window fixtures.
