from __future__ import annotations

import json
import sys
from pathlib import Path


HARNESS_DIR = Path(__file__).resolve().parents[2]
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

BASE_JUDGE_PROMPT = """You are an expert LongBanana image-generation judge.

Judge the candidate image strictly against the task definition and attached
reference images. Use only visible evidence. If evidence is ambiguous or not
visible, answer "uncertain".

Available MCP tools on the `image-gen` server:
  - view_reference_image

Use `view_reference_image` when you need to inspect the candidate or a
reference image. Do not generate, edit, copy, or delete images.

Gemini vision requirements:
- You must inspect the candidate image before answering.
- For non-global checks, inspect every listed reference image before answering.
- Do not answer from filenames, paths, or task text alone.

When finished, output exactly one answer block:
<answer>
{"answer": "one option from the task options", "reason": "brief visible-evidence reason", "evidence": ["short visible evidence"]}
</answer>
"""


OPENCLAW_NATIVE_JUDGE_PROMPT = """You are an expert LongBanana image-generation judge.

Judge the candidate image strictly against the task definition and attached
reference images. Use only visible evidence. If evidence is ambiguous or not
visible, answer "uncertain".

OpenClaw native image input:
- The candidate and reference image paths listed below are automatically
  attached to the vision model for this turn.
- Do not call tools to inspect images; judge only from the attached images and
  task JSON.
- Do not generate, edit, copy, save, or delete images.

Gemini vision requirements:
- You must inspect the candidate image before answering.
- For non-global checks, inspect every listed reference image before answering.
- Do not answer from filenames, paths, or task text alone.

When finished, output exactly one answer block:
<answer>
{"answer": "one option from the task options", "reason": "brief visible-evidence reason", "evidence": ["short visible evidence"]}
</answer>
"""

OPENCLAW_SUBAGENT_JUDGE_PROMPT = """You are an expert LongBanana image-generation judge.

Judge the candidate image strictly against the task definition and attached
reference images. Use only visible evidence. If evidence is ambiguous or not
visible, answer "uncertain".

OpenClaw visual subagent mode:
- The candidate and reference image paths listed below are automatically
  attached to the vision model for this turn.
- Use sessions_spawn only when OCR, object counting, layout checking, or
  identity/feature matching evidence would improve the judgment.
- For every non-global check, spawn exactly one most relevant specialized
  visual subagent before the final answer unless the question explicitly
  requires multiple independent visual modules.
- Delegate OCR evidence to agentId "ocr-judge".
- Delegate object presence/counting evidence to agentId "detector-judge".
- Delegate spatial/layout evidence to agentId "layout-judge".
- Delegate reference identity/feature evidence to agentId "identity-judge".
- For object count questions, prefer detector-judge. For reference identity or
  feature matching questions, prefer identity-judge.
- Pass the candidate path, reference paths, task question, guide, options, and
  the exact evidence request in every child task so the child run receives the
  same visible image context.
- When calling sessions_spawn, set thinking to exactly "high" or omit it; put
  rationale and evidence instructions in task, never in thinking.
- Subagent completion is push-based. After spawning children, wait for their
  completion messages; use subagents or session_status only for an on-demand
  status check.
- Do not call sessions_spawn again for the same evidence request after an
  accepted or pending child run. Do not retry failed spawns inside the same
  judgment. Do not claim a gateway timeout unless a tool result explicitly says
  that exact error.
- Do not generate, edit, copy, save, or delete images.
- Do not output the final answer until the needed subagent completion evidence has arrived.

Gemini vision requirements:
- You must inspect the candidate image before answering.
- For non-global checks, inspect every listed reference image before answering.
- Do not answer from filenames, paths, or task text alone.

When finished, output exactly one answer block:
<answer>
{"answer": "one option from the task options", "reason": "brief visible-evidence reason", "evidence": ["short visible evidence"], "subagent_evidence": {"ocr": [], "detection": [], "layout": [], "identity": []}}
</answer>
"""


JUDGE_STRATEGY_PROMPTS = {
    "react": (
        "ReAct judge procedure:\n"
        "1. Thought: identify the next visual fact needed to answer the judge question.\n"
        "2. Action: inspect the candidate image and the required reference images with view_reference_image.\n"
        "3. Observation: record only visible evidence that affects the selected answer option.\n"
        "4. Repeat until the visible evidence is sufficient, then output the answer block."
    ),
    "plan-and-execute": (
        "Plan-and-execute judge procedure:\n"
        "1. Plan: decompose the question, guide, options, and reference requirements into concrete visual checks.\n"
        "2. Execute: inspect the candidate and each listed reference image required by the task.\n"
        "3. Compare: match visible candidate evidence against the option descriptions.\n"
        "4. Judge decision: output the single best option with brief visible evidence."
    ),
    "reflection": (
        "Reflection judge procedure:\n"
        "1. Draft: after inspecting the candidate and references, draft the likely answer and evidence.\n"
        "2. Self-check: verify the draft against the question, guide, options, and visible image evidence.\n"
        "3. Revise: if any evidence is ambiguous, missing, or contradicted, change the answer to the appropriate option.\n"
        "4. Judge decision: output exactly one final answer block."
    ),
    "pipe": (
        "Pipe judge procedure:\n"
        "Stage 1: ReAct\n"
        "1. Identify which visible facts are needed to answer the question.\n"
        "2. Inspect the candidate and required reference images with view_reference_image.\n"
        "3. Record concise observations keyed by candidate or reference filename.\n\n"
        "Stage 2: Plan-and-Execute\n"
        "1. Build a compact checklist from the question, guide, and option descriptions.\n"
        "2. Compare candidate evidence against each required reference identity, attribute, and relationship.\n"
        "3. Select the best answer option supported by visible evidence.\n\n"
        "Stage 3: Reflection\n"
        "1. Self-check the selected answer against the task options and visible evidence.\n"
        "2. If evidence is ambiguous or missing, prefer the task's uncertain option.\n"
        "3. Judge decision: output exactly one final answer block."
    ),
}


JUDGE_STRATEGY_CONTRACT = """Judge strategy contract:
- Use only the tool names and schemas from the judge prompt; do not invent new tools.
- Inspect images through view_reference_image; do not generate, edit, copy, save, or delete images.
- Work from the task JSON, candidate image, and listed reference files only.
- For non-global checks, inspect every listed reference image before answering.
- Keep notes concise and grounded in visible evidence.
- Choose exactly one answer from the task options."""


OPENCLAW_JUDGE_STRATEGY_CONTRACT = """Judge strategy contract:
- Do not call tools; the candidate and reference images are already attached to the vision model.
- Do not generate, edit, copy, save, or delete images.
- Work from the task JSON, candidate image, and listed reference files only.
- For non-global checks, inspect every listed reference image before answering.
- Keep notes concise and grounded in visible evidence.
- Choose exactly one answer from the task options."""

OPENCLAW_SUBAGENT_JUDGE_STRATEGY_CONTRACT = """Judge strategy contract:
- Use only sessions_spawn for specialized visual evidence delegation; do not invent tools.
- Spawn exactly one most relevant specialized agent for each non-global check unless multiple independent modules are explicitly required.
- Use only these specialized agents: ocr-judge, detector-judge, layout-judge, identity-judge.
- When calling sessions_spawn, set thinking to exactly "high" or omit it; put rationale and evidence instructions in task.
- After spawning, wait for subagent completion messages; use subagents or session_status only for on-demand status checks.
- Do not repeat sessions_spawn for the same evidence request after an accepted or pending child run.
- Do not invent gateway timeout evidence; mention gateway errors only when returned by a tool.
- Do not output the final answer until the needed subagent completion evidence has arrived.
- Work from the task JSON, candidate image, listed reference files, and subagent evidence only.
- For non-global checks, inspect every listed reference image before answering.
- Keep notes concise and grounded in visible evidence.
- Choose exactly one answer from the task options."""


OPENCLAW_STRATEGY_PROMPTS = {
    key: value.replace(
        "with view_reference_image",
        "directly from the attached image inputs",
    ).replace(
        "through view_reference_image",
        "directly from the attached image inputs",
    )
    for key, value in JUDGE_STRATEGY_PROMPTS.items()
}


def build_base_judge_prompt(task: dict, base_prompt: str = BASE_JUDGE_PROMPT) -> str:
    refs = task.get("refs", []) or []
    refs_block = "\n".join(f"  - {p}" for p in refs) if refs else "  - none"
    payload = {
        "harness": task.get("harness", ""),
        "backend": task.get("backend", ""),
        "case_id": task.get("case_id", ""),
        "data_index": task.get("data_index", ""),
        "category": task.get("category", ""),
        "scene": task.get("scene", ""),
        "question": task.get("question", ""),
        "guide": task.get("guide", ""),
        "options": task.get("options", []),
        "option_desc": task.get("option_desc", {}),
        "image_order": (
            "Candidate image is the generated result being judged. "
            "Reference images are attached only for non-global checks."
        ),
    }
    return (
        f"{base_prompt.rstrip()}\n\n"
        f"Candidate image:\n  - {task.get('candidate_path', '')}\n\n"
        f"Reference images:\n{refs_block}\n\n"
        f"Judge task JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
    )


def _build_agent_judge_prompt(
    task: dict,
    strategy_name: str,
    *,
    base_prompt_text: str,
    strategy_contract: str,
    strategy_prompts: dict[str, str],
) -> str:
    base_prompt = build_base_judge_prompt(task, base_prompt_text)
    try:
        strategy_prompt = strategy_prompts[strategy_name]
    except KeyError as exc:
        known = ", ".join(strategy_prompts)
        raise ValueError(f"unknown agent judge strategy {strategy_name!r}; known strategies: {known}") from exc

    title = {
        "react": "ReAct",
        "plan-and-execute": "Plan-and-Execute",
        "reflection": "Reflection",
        "pipe": "ReAct -> Plan-and-Execute -> Reflection",
    }[strategy_name]
    return (
        f"{base_prompt.rstrip()}\n\n"
        f"Agent strategy: {strategy_name} ({title})\n"
        "Applies to harness: opencode-agent-judge\n\n"
        f"{strategy_contract}\n\n"
        f"{strategy_prompt}\n"
    )


def build_agent_judge_prompt(task: dict, strategy_name: str) -> str:
    return _build_agent_judge_prompt(
        task,
        strategy_name,
        base_prompt_text=BASE_JUDGE_PROMPT,
        strategy_contract=JUDGE_STRATEGY_CONTRACT,
        strategy_prompts=JUDGE_STRATEGY_PROMPTS,
    )


def build_openclaw_agent_judge_prompt(task: dict, strategy_name: str) -> str:
    return _build_agent_judge_prompt(
        task,
        strategy_name,
        base_prompt_text=OPENCLAW_NATIVE_JUDGE_PROMPT,
        strategy_contract=OPENCLAW_JUDGE_STRATEGY_CONTRACT,
        strategy_prompts=OPENCLAW_STRATEGY_PROMPTS,
    )


def build_openclaw_subagent_judge_prompt(task: dict, strategy_name: str) -> str:
    return _build_agent_judge_prompt(
        task,
        strategy_name,
        base_prompt_text=OPENCLAW_SUBAGENT_JUDGE_PROMPT,
        strategy_contract=OPENCLAW_SUBAGENT_JUDGE_STRATEGY_CONTRACT,
        strategy_prompts=OPENCLAW_STRATEGY_PROMPTS,
    )
