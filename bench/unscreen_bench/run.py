"""Benchmark runner: UnScreen's reconstruction vs a Tesseract baseline on fixture frames.

Usage (from bench/):
  PYTHONPATH=. uv run --project ../services/engine python -m unscreen_bench.run \
      --kinds sheet --variants 1080p-degraded --limit 10 --name kill

Every number written here is measured on this run; nothing is estimated."""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.config import get_settings
from engine.llm.client import ModelError, build_model
from engine.pipeline.session import SessionPipeline
from unscreen_bench.ocr import OCR_CONFIGS, grid, lines, run_tesseract
from unscreen_bench.score import PredCell, Score, score_document, score_grid, score_lines

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "fixtures" / "frames"
RESULTS = ROOT / "results"


@dataclass
class FrameResult:
    id: str
    kind: str
    variant: str
    unscreen: Score | None
    ocr: Score
    ocr_by_config: dict[str, Score]
    latency_ms: int | None
    calls: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    error: str | None


def frame_path(item: dict[str, Any]) -> Path:
    ext = ".jpg" if item["variant"] == "1080p-degraded" else ".png"
    return FRAMES / f"{item['id']}{ext}"


def ocr_score(path: Path, truth: dict[str, Any], psm: int, upscale: int) -> Score:
    words = run_tesseract(path, psm, upscale)
    kind = truth["content_type"]
    if kind == "sheet":
        rows = grid(words)
        headers = truth["sheet"]["columns"]
        # Generous: take the OCR line that best matches the true header row as the header.
        best, best_hits = 0, -1
        for i, r in enumerate(rows):
            hits = sum(1 for c in r if c.text.strip() in headers)
            if hits > best_hits:
                best, best_hits = i, hits
        header = rows[best] if rows else []
        body = rows[best + 1 :] if rows else []
        return score_grid(headers, truth["sheet"]["rows"], header, body, "sheet")
    flat = [PredCell(text=" ".join(w.text for w in ln), confident=True, flagged=False) for ln in lines(words)]
    if kind == "code":
        return score_lines([ln["text"].rstrip() for ln in truth["code"]["lines"]], flat)
    return score_lines([b["text"] for b in truth["blocks"]], flat, kind="blocks", exact_whitespace=False)


async def run_one(item: dict[str, Any], sem: asyncio.Semaphore) -> FrameResult:
    path = frame_path(item)
    truth = json.loads((FRAMES / f"{item['id']}.truth.json").read_text())
    ocr_by_config = {
        f"psm{p}x{u}": await asyncio.to_thread(ocr_score, path, truth, p, u) for p, u in OCR_CONFIGS
    }
    ocr = ocr_by_config["psm3x1"]
    settings = get_settings()
    pipe = SessionPipeline(build_model(settings), settings)
    async with sem:
        started = time.perf_counter()
        try:
            out = await pipe.process(path.read_bytes())
            latency = int((time.perf_counter() - started) * 1000)
            score = score_document(truth, out.doc)
            error = None
        except ModelError as exc:
            latency, score, error = None, None, str(exc)
    m = pipe.meter
    return FrameResult(
        id=item["id"],
        kind=item["kind"],
        variant=item["variant"],
        unscreen=score,
        ocr=ocr,
        ocr_by_config=ocr_by_config,
        latency_ms=latency,
        calls=m.calls,
        cost_usd=m.usd,
        input_tokens=m.input_tokens,
        output_tokens=m.output_tokens + m.thought_tokens,
        error=error,
    )


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = max(0, min(len(xs) - 1, round(q * (len(xs) - 1))))
    return xs[k]


def aggregate(results: list[FrameResult]) -> dict[str, Any]:
    def pool(scores: list[Score]) -> dict[str, float | int]:
        total = Score(kind="pool")
        for s in scores:
            for f in ("truth_items", "exact", "char_errors", "truth_chars", "predicted_confident", "hallucinated",
                      "found_anywhere", "placed_correctly", "flagged", "flagged_wrong"):
                setattr(total, f, getattr(total, f) + getattr(s, f))
        return {
            "frames": len(scores),
            "items": total.truth_items,
            "exact_match": round(total.exact_rate, 4),
            "cer": round(total.cer, 4),
            "hallucination_rate": round(total.hallucination_rate, 4),
            "structure_accuracy": round(total.structure_rate, 4),
            "text_recall": round(total.found_anywhere / total.truth_items, 4) if total.truth_items else 0.0,
            "flagged": total.flagged,
            "flagged_wrong": total.flagged_wrong,
        }

    ok = [r for r in results if r.unscreen is not None]
    by_config = {k: pool([r.ocr_by_config[k] for r in results]) for k in results[0].ocr_by_config} if results else {}
    best = max(by_config, key=lambda k: (by_config[k]["exact_match"], by_config[k]["text_recall"])) if by_config else None
    lat = [float(r.latency_ms) for r in ok if r.latency_ms is not None]
    return {
        "unscreen": pool([r.unscreen for r in ok if r.unscreen]),
        "ocr": by_config[best] if best else pool([]),
        "ocr_config": best,
        "ocr_by_config": by_config,
        "content_type_accuracy": round(sum(1 for r in ok if r.unscreen and r.unscreen.content_type_ok) / len(ok), 4) if ok else 0.0,
        "errors": len(results) - len(ok),
        "latency_ms": {"p50": statistics.median(lat) if lat else None, "p95": pct(lat, 0.95), "max": max(lat) if lat else None},
        "cost_usd_per_frame": round(sum(r.cost_usd for r in ok) / len(ok), 6) if ok else None,
        "calls_per_frame": round(sum(r.calls for r in ok) / len(ok), 2) if ok else None,
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", default="sheet,code,slide")
    ap.add_argument("--variants", default="720p,1080p,1080p-degraded")
    ap.add_argument("--limit", type=int, default=0, help="max frames per kind and variant")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--name", default="full")
    args = ap.parse_args()
    kinds, variants = args.kinds.split(","), args.variants.split(",")
    manifest = json.loads((FRAMES / "manifest.json").read_text())
    chosen: list[dict[str, Any]] = []
    for kind in kinds:
        for variant in variants:
            items = [m for m in manifest if m["kind"] == kind and m["variant"] == variant]
            chosen += items[: args.limit] if args.limit else items
    sem = asyncio.Semaphore(args.concurrency)
    results = await asyncio.gather(*(run_one(i, sem) for i in chosen))
    settings = get_settings()
    report: dict[str, Any] = {
        "name": args.name,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "models": {
            "reconstruct": settings.reconstruct_model,
            "verify": settings.verify_model,
            "thinking_level": settings.thinking_level,
            "image_resolution": settings.image_resolution,
        },
        "llm_mode": settings.llm_mode,
        "groups": {},
        "frames": [],
    }
    for kind in kinds:
        for variant in variants:
            group = [r for r in results if r.kind == kind and r.variant == variant]
            if group:
                report["groups"][f"{kind}/{variant}"] = aggregate(group)
    report["overall"] = aggregate(list(results))
    for r in results:
        report["frames"].append(
            {
                "id": r.id,
                "latency_ms": r.latency_ms,
                "calls": r.calls,
                "cost_usd": round(r.cost_usd, 6),
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "error": r.error,
                "unscreen": r.unscreen.to_json() if r.unscreen else None,
                "ocr": {k: v.to_json() for k, v in r.ocr_by_config.items()},
            }
        )
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{datetime.now(UTC).strftime('%Y-%m-%d')}-{args.name}.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k in ("groups", "overall", "models")}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
