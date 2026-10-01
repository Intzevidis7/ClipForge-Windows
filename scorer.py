"""Local Ollama scorer using transcript line indexes instead of hallucinated timestamps."""
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from transcriber import Segment


PROMPT = """You are selecting short clips from a Greek-language stream transcript.

The transcript is a numbered list. Choose at most TWO genuinely interesting standalone moments:
- funny jokes or reactions;
- exciting or emotional moments;
- surprising statements;
- strong quotable moments.

Ignore filler, greetings, repeated words, garbled text, and ordinary conversation.
Do not pad the list.

Important:
- Use the NUMBERED LINE indexes, not timestamps.
- Each selected moment must cover multiple consecutive lines.
- Return a start_line and end_line.
- Do not return seconds.
- Return only valid JSON in this exact shape:
{{"clips":[{{"start_line":12,"end_line":20,"title":"short title","score":8,"reason":"short reason"}}]}}

Scores:
- 9-10 exceptional and rare;
- 7-8 clearly strong;
- 6 mildly interesting;
- below 6 should not be returned.

Transcript:
{transcript}
"""


@dataclass
class Candidate:
    start: float
    end: float
    title: str
    score: float
    reason: str
    text: str


def _chunks(segments, seconds=180.0):
    chunk = []
    chunk_start = None

    for segment in segments:
        if chunk_start is None:
            chunk_start = segment.start

        if chunk and segment.end - chunk_start > seconds:
            yield chunk
            chunk = []
            chunk_start = segment.start

        chunk.append(segment)

    if chunk:
        yield chunk


def _write_atomic(path: Path, data: dict):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def _parse_response(response_text, chunk, min_len, max_len, min_score):
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return [], False

    items = data.get("clips", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        return [], False

    candidates = []

    for item in items[:2]:
        if not isinstance(item, dict):
            continue

        try:
            start_line = int(item["start_line"])
            end_line = int(item["end_line"])
            score = float(item["score"])
        except (KeyError, TypeError, ValueError):
            continue

        if not math.isfinite(score):
            continue

        if start_line < 1 or end_line < start_line or end_line > len(chunk):
            continue

        start_segment = chunk[start_line - 1]
        end_segment = chunk[end_line - 1]
        start = start_segment.start
        end = end_segment.end

        if end <= start:
            continue

        if end - start > max_len + 5:
            continue

        if score < min_score or score > 10:
            continue

        text = " ".join(
            segment.text
            for segment in chunk[start_line - 1:end_line]
        )

        candidates.append(
            Candidate(
                start=start,
                end=end,
                title=str(item.get("title", "Clip"))[:100],
                score=score,
                reason=str(item.get("reason", ""))[:200],
                text=text,
            )
        )

    return candidates, True


def score_moments(
    segments,
    min_len,
    max_len,
    llm_model="llama3.2:3b",
    ollama_host="http://localhost:11434",
    min_score=6.0,
    timeout=300,
    cache_dir=None,
    retry_failed=False,
):
    cache_dir = Path(cache_dir or "scoring_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    chunks = list(_chunks(segments))
    all_candidates = []

    for chunk_number, chunk in enumerate(chunks, start=1):
        numbered_lines = "\n".join(
            f"{line_number}: [{segment.start:.1f}-{segment.end:.1f}] {segment.text}"
            for line_number, segment in enumerate(chunk, start=1)
        )

        prompt = PROMPT.format(transcript=numbered_lines)

        digest = hashlib.sha256(
            json.dumps(
                {
                    "prompt": prompt,
                    "model": llm_model,
                    "min_score": min_score,
                    "version": 2,
                },
                ensure_ascii=False,
            ).encode()
        ).hexdigest()[:16]

        cache_file = cache_dir / f"chunk_{chunk_number:03d}_{digest}.json"

        if cache_file.exists() and not retry_failed:
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if cached.get("status") == "ok":
                    cached_candidates = [
                        Candidate(**candidate)
                        for candidate in cached.get("candidates", [])
                    ]
                    all_candidates.extend(cached_candidates)
                    print(
                        f"  [{chunk_number}/{len(chunks)}] cached: "
                        f"{len(cached_candidates)} candidates",
                        flush=True,
                    )
                    continue

                if cached.get("status") == "failed":
                    print(
                        f"  [{chunk_number}/{len(chunks)}] previous failure skipped",
                        flush=True,
                    )
                    continue

            except (OSError, ValueError, TypeError, KeyError):
                pass

        try:
            response = requests.post(
                ollama_host.rstrip("/") + "/api/generate",
                json={
                    "model": llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.2,
                        "num_ctx": 4096,
                        "num_predict": 300,
                    },
                },
                timeout=(10, timeout),
            )
            response.raise_for_status()

            body = response.json()
            candidates, valid = _parse_response(
                body.get("response", ""),
                chunk,
                min_len,
                max_len,
                min_score,
            )

            if not valid:
                raise ValueError("Ollama returned invalid JSON")

            _write_atomic(
                cache_file,
                {
                    "status": "ok",
                    "candidates": [asdict(candidate) for candidate in candidates],
                },
            )

            all_candidates.extend(candidates)

            print(
                f"  [{chunk_number}/{len(chunks)}] saved "
                f"{len(candidates)} candidates",
                flush=True,
            )

        except (requests.RequestException, ValueError, TypeError) as error:
            _write_atomic(
                cache_file,
                {
                    "status": "failed",
                    "error": str(error),
                    "candidates": [],
                },
            )

            print(
                f"  [{chunk_number}/{len(chunks)}] failed: {error}",
                flush=True,
            )

    return sorted(
        all_candidates,
        key=lambda candidate: candidate.score,
        reverse=True,
    )


def dedupe_overlapping(candidates, max_clips):
    selected = []

    for candidate in candidates:
        overlaps = any(
            not (
                candidate.end <= existing.start
                or candidate.start >= existing.end
            )
            for existing in selected
        )

        if not overlaps:
            selected.append(candidate)

        if len(selected) >= max_clips:
            break

    return sorted(selected, key=lambda candidate: candidate.start)
