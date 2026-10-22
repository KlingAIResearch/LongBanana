from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


PASS_ANSWERS = {"match", "correct", "pass"}
FAIL_ANSWERS = {"mismatch_or_missing", "incorrect", "fail"}
_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.S)
_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


@dataclass(frozen=True)
class ParsedAnswer:
    answer: str
    is_pass: bool
    is_uncertain: bool
    is_invalid: bool
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    error_msg: str = ""
    raw_head: str = ""


def _loads_answer_body(body: str) -> dict:
    body = body.strip()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        if '\\"' not in body and "\\n" not in body:
            raise
    unescaped = bytes(body, "utf-8").decode("unicode_escape").strip()
    return json.loads(unescaped)


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _valid_answer(payload: dict, options: set[str] | None) -> bool:
    if options is None:
        return True
    return str(payload.get("answer", "")).strip() in options


def _extract_answer_blocks(text: str) -> list[str]:
    clean_text = _strip_ansi(text or "")
    bodies: list[str] = []
    lines = clean_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if "<answer>" not in line or "text=<answer>" in line or "[ws]" in line:
            index += 1
            continue
        after = line.split("<answer>", 1)[1]
        if "</answer>" in after:
            bodies.append(after.split("</answer>", 1)[0])
            index += 1
            continue
        captured = [after] if after.strip() else []
        index += 1
        while index < len(lines):
            current = lines[index]
            if "</answer>" in current:
                before = current.split("</answer>", 1)[0]
                if before.strip():
                    captured.append(before)
                bodies.append("\n".join(captured))
                break
            captured.append(current)
            index += 1
        index += 1

    for match in _ANSWER_RE.finditer(clean_text):
        body = match.group(1)
        if body not in bodies:
            bodies.append(body)
    return bodies


def _payload_from_answer_blocks(text: str, options: set[str] | None) -> dict | None:
    fallback: dict | None = None
    for body in reversed(_extract_answer_blocks(text)):
        try:
            payload = _loads_answer_body(body)
        except Exception:
            continue
        if fallback is None:
            fallback = payload
        if _valid_answer(payload, options):
            return payload
    return fallback


def _extract_payload(text: str, options: set[str] | None = None) -> dict:
    decoder = json.JSONDecoder()
    wrapped_values = []
    raw_text = _strip_ansi(text or "")
    try:
        wrapped_values.append(json.loads(raw_text))
    except Exception:
        for match in re.finditer(r"{", raw_text):
            try:
                value, _ = decoder.raw_decode(raw_text[match.start():])
            except Exception:
                continue
            wrapped_values.append(value)

    for wrapped in reversed(wrapped_values):
        if not isinstance(wrapped, dict):
            continue
        for key in ("finalAssistantVisibleText", "finalAssistantRawText"):
            value = wrapped.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    return _extract_payload(value, options)
                except Exception:
                    continue
        payloads = wrapped.get("payloads")
        if isinstance(payloads, list):
            for item in reversed(payloads):
                if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
                    try:
                        return _extract_payload(item["text"], options)
                    except Exception:
                        continue
        meta = wrapped.get("meta")
        if isinstance(meta, dict):
            for key in ("finalAssistantVisibleText", "finalAssistantRawText"):
                value = meta.get(key)
                if isinstance(value, str) and value.strip():
                    try:
                        return _extract_payload(value, options)
                    except Exception:
                        continue
        if "answer" in wrapped:
            if _valid_answer(wrapped, options):
                return wrapped

    payload = _payload_from_answer_blocks(raw_text, options)
    if payload is not None:
        return payload

    if wrapped_values:
        for wrapped in reversed(wrapped_values):
            if isinstance(wrapped, dict) and "answer" in wrapped:
                return wrapped
    return _loads_answer_body(raw_text.strip())


def parse_agent_answer(text: str, options: list[str]) -> ParsedAnswer:
    raw_head = (text or "")[:240].replace("\n", " ")
    option_set = set(options)
    try:
        payload = _extract_payload(text, option_set)
    except Exception as exc:
        return ParsedAnswer(
            answer="uncertain",
            is_pass=False,
            is_uncertain=True,
            is_invalid=True,
            error_msg=f"parse_failed:{type(exc).__name__}",
            raw_head=raw_head,
        )

    answer = str(payload.get("answer", "")).strip()
    if answer not in options:
        return ParsedAnswer(
            answer="uncertain",
            is_pass=False,
            is_uncertain=True,
            is_invalid=True,
            reason=str(payload.get("reason", "")),
            error_msg=f"invalid_answer:{answer[:80]}",
            raw_head=raw_head,
        )

    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = [str(evidence)]

    return ParsedAnswer(
        answer=answer,
        is_pass=answer in PASS_ANSWERS,
        is_uncertain=answer == "uncertain",
        is_invalid=False,
        reason=str(payload.get("reason", "")),
        evidence=[str(item) for item in evidence],
        raw_head=raw_head,
    )
