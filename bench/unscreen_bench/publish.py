"""Copy measured benchmark aggregates into the web app (README tables come from the same file).

Usage (from bench/): PYTHONPATH=. uv run --project ../services/engine python -m unscreen_bench.publish
Reads bench/results/*.json; writes apps/web/src/lib/bench/summary.json. Only measured values
are copied; a missing run is simply absent."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TARGET = ROOT.parent / "apps" / "web" / "src" / "lib" / "bench" / "summary.json"
README = ROOT.parent / "README.md"
START, END = "<!-- bench:start -->", "<!-- bench:end -->"
VARIANTS = {"720p": "720p", "1080p": "1080p", "1080p-degraded": "meeting window, 720p, lossy"}


def latest(pattern: str) -> tuple[str, dict[str, Any]] | None:
    files = sorted(RESULTS.glob(pattern))
    if not files:
        return None
    return files[-1].name, json.loads(files[-1].read_text())


def reconstruct_summary(name: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "file": f"bench/results/{name}",
        "run_at": data["run_at"],
        "models": data["models"],
        "overall": data["overall"],
        "groups": data["groups"],
        "frames": len(data["frames"]),
    }


def live_summary(name: str, data: dict[str, Any]) -> dict[str, Any]:
    keys = ("run_at", "kind", "edit_interval_ms", "first_snapshot_ms", "truth_changes", "recall", "precision",
            "change_to_announce_ms", "final_dom_vs_truth")
    errors = [e for e in data.get("engine_events", []) if "error" in e]
    return {
        "file": f"bench/results/{name}",
        **{k: data.get(k) for k in keys},
        "engine_errors": len(errors),
        "never_read": data.get("first_snapshot_ms") is None,
    }


def pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


def readme_section(out: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, title in (("full", "Full benchmark"), ("kill", "Kill test (10 spreadsheets in a meeting window)")):
        run = out.get(key)
        if not run:
            continue
        checked = (
            f"cross-checked by `{run['models']['verify']}`"
            if run["models"].get("cross_check")
            else "no cross-check read (added after this run)"
        )
        lines += [
            f"**{title}**, {run['run_at'][:10]}, reads by `{run['models']['reconstruct']}`, {checked}:",
            "",
            "| Frames | Read | Exact (UnScreen) | Exact (OCR) | Wrong as fact (UnScreen) | Wrong as fact (OCR) | Right place (UnScreen) | Right place (OCR) |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for g, a in run["groups"].items():
            kind, variant = g.split("/")
            u, o = a["unscreen"], a["ocr"]
            lines.append(
                f"| {kind}, {VARIANTS.get(variant, variant)} | {u['frames']} of {u['frames'] + a['errors']} "
                f"| {pct(u['exact_match'])} | {pct(o['exact_match'])} | {pct(u['hallucination_rate'])} "
                f"| {pct(o['hallucination_rate'])} | {pct(u['structure_accuracy'])} | {pct(o['structure_accuracy'])} |"
            )
        lat = run["overall"]["latency_ms"]
        cost = run["overall"]["cost_usd_per_frame"]
        timing = (
            f"Reconstruction time per frame: median {lat['p50'] / 1000:.1f} s, p95 {lat['p95'] / 1000:.1f} s. "
            f"Cost per frame: ${cost:.4f}."
            if lat["p50"] is not None and cost is not None
            else "Latency: not measured."
        )
        lines += ["", timing, ""]
    if pipe := out.get("pipeline"):
        lines.append(
            f"**Without the model** ({pipe['run_at'][:10]}): with a scripted model answering instantly, an edit is spoken "
            f"{pipe['p50_ms'] / 1000:.1f} s later (median of {pipe['edits']} edits, max {pipe['max_ms'] / 1000:.1f} s). "
            "This is UnScreen's own share of the latency: capture, change gate, engine and announcement coalescing."
        )
        lines.append("")
    for live in out.get("live", []):
        if live["never_read"]:
            lines.append(
                f"**Live loop** ({live['kind']}, {live['run_at'][:10]}): no frame was read; the API returned "
                f"rate-limit errors and timeouts ({live['engine_errors']} engine "
                f"{'error' if live['engine_errors'] == 1 else 'errors'}). Nothing was announced."
            )
            lines.append("")
            continue
        c = live["change_to_announce_ms"]
        median = "n/a" if c["p50"] is None else f"{c['p50'] / 1000:.1f} s"
        final = live["final_dom_vs_truth"]
        lines.append(
            f"**Live loop** ({live['kind']}, {live['run_at'][:10]}): {live['truth_changes']} scripted changes, "
            f"recall {pct(live['recall'])}, precision {pct(live['precision'])}, change to announcement median "
            f"{median}"
            + (f", final table {final['ok']} of {final['total']} cells correct." if final else ".")
        )
        lines.append("")
    lines.append("OCR is Tesseract 5.5 (best of three settings) with help to find table cells; screen reader OCR gets none.")
    return "\n".join(lines)


def main() -> None:
    out: dict[str, Any] = {}
    if full := latest("*-full.json"):
        out["full"] = reconstruct_summary(*full)
    if kill := latest("*-kill-v4.json"):
        out["kill"] = reconstruct_summary(*kill)
    live = [live_summary(p.name, json.loads(p.read_text())) for p in sorted(RESULTS.glob("*-live-*.json"))]
    if live:
        out["live"] = live
    if overhead := latest("*-pipeline-overhead.json"):
        name, data = overhead
        out["pipeline"] = {"file": f"bench/results/{name}", **{k: data[k] for k in ("run_at", "note", "edits", "latencies_ms", "p50_ms", "max_ms")}}
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(out, indent=1) + "\n")
    readme = README.read_text()
    if START in readme and END in readme:
        head, rest = readme.split(START, 1)
        _, tail = rest.split(END, 1)
        README.write_text(f"{head}{START}\n{readme_section(out)}\n{END}{tail}")
    print(f"wrote {TARGET} and README results: {', '.join(out) or 'nothing'}")


if __name__ == "__main__":
    main()
