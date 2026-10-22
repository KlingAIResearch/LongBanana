"""Reusable agent strategy prompts for image-generation harnesses.

The strategy layer is intentionally harness-agnostic: each agent harness keeps
its native tools and runner, while this module only wraps the task prompt with a
planning policy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentStrategy:
    name: str
    title: str
    instructions: str


PIPE_GENERATION_MODES = ("multi", "final_once")

_COMMON_INSTRUCTIONS = """Strategy contract:
- Use the tool names and schemas from the harness prompt; do not invent new tools.
- Work from the target description and the listed on-disk files only.
- For many-reference cases, inspect references in small batches, keep short notes keyed by filename, and stop inspecting when the selected references cover the target constraints.
- Track count, identity, layout, style, text-free rendering, and any required relationships between objects.
- Follow the active strategy's generation-count rule.
- Save the final image only through the provided image-generation tool and output directory.
"""


_STRATEGIES: dict[str, AgentStrategy] = {
    "react": AgentStrategy(
        name="react",
        title="ReAct",
        instructions="""ReAct procedure:
1. Thought: identify the next missing visual fact needed for the target.
2. Action: inspect a small batch of promising reference images.
3. Observation: summarize only the facts that affect reference selection or prompt construction.
4. Repeat until the key target constraints are covered, then call the image-generation tool.
Keep the loop tight; do not exhaustively inspect every reference when the evidence is already sufficient.""",
    ),
    "plan-and-execute": AgentStrategy(
        name="plan-and-execute",
        title="Plan-and-Execute",
        instructions="""Plan-and-execute procedure:
1. Plan: decompose the target into required visual constraints, likely reference categories, and generation risks.
2. Select: choose which reference files to inspect first and why.
3. Execute: inspect the selected references, revise the reference shortlist, and build the final generation prompt.
4. Generate: call the image-generation tool with the selected references and a prompt that explicitly covers the plan constraints.
Keep the plan concise and update it only when reference observations change the decision.""",
    ),
    "reflection": AgentStrategy(
        name="reflection",
        title="Reflection",
        instructions="""Reflection procedure:
1. Draft: after inspecting enough references, draft the final prompt and selected reference list.
2. Self-check: compare the draft against the target description for missing counts, missing entities, wrong attributes, layout conflicts, and backend limitations.
3. Revise: fix the prompt/reference list before generation.
4. Generate: call the image-generation tool once with the revised prompt and selected references.
The reflection is a pre-generation quality gate, not an invitation to generate multiple alternatives.""",
    ),
    "pipe": AgentStrategy(
        name="pipe",
        title="ReAct -> Plan-and-Execute -> Reflection",
        instructions="""Pipe procedure:
Stage 1: ReAct
1. Inspect reference images in small batches.
2. Record concise observations keyed by filename, focusing only on visual facts needed for the target.
3. Stop when observations cover the required identities, counts, layout, style, and relationships.

Stage 2: Plan-and-Execute
1. Build a reference shortlist from the Stage 1 observations.
2. Write a compact plan for layout, counts, object identities, style, and major generation risks.
3. Draft the image-generation prompt from the plan and shortlist.

Stage 3: Reflection
1. Self-check the observations, shortlist, plan, and draft prompt for missing entities, wrong counts, attribute drift, layout conflicts, style mismatch, and backend limitations.
2. Revise the shortlist and prompt before the final accepted output.
3. Use only the tools declared by the harness prompt when inspecting references or generating images.""",
    ),
}

DEFAULT_STRATEGIES = ("pipe",)


def parse_pipe_generation_mode(value: str | None) -> str:
    mode = (value or "multi").strip() or "multi"
    if mode not in PIPE_GENERATION_MODES:
        known = ", ".join(PIPE_GENERATION_MODES)
        raise ValueError(f"invalid PIPE_GENERATION_MODE {mode!r}; known modes: {known}")
    return mode


def known_strategy_names() -> tuple[str, ...]:
    return tuple(_STRATEGIES)


def parse_strategy_names(value: str | None) -> tuple[str, ...]:
    if value is None or not value.strip():
        return DEFAULT_STRATEGIES
    names = tuple(part.strip() for part in value.split(",") if part.strip())
    unknown = [name for name in names if name not in _STRATEGIES]
    if unknown:
        known = ", ".join(known_strategy_names())
        raise ValueError(f"unknown agent strategy {unknown[0]!r}; known strategies: {known}")
    return names


def _pipe_generation_instructions(mode: str) -> str:
    if mode == "multi":
        return """Pipe generation mode: multi
- After Stage 2, you may generate a candidate image using the harness image-generation tool.
- Whenever the tool returns a visible output path, inspect the candidate against the complete target before accepting it.
- If the candidate does not satisfy the target, revise the prompt and/or reference shortlist and generate again.
- You decide how many generation-and-inspection rounds are needed. There is no fixed generation-count limit; stop only when you judge the target is satisfied or the harness wall-clock budget ends."""
    if mode == "final_once":
        return """Pipe generation mode: final_once
- Do not call the image-generation tool during Stage 1 or Stage 2.
- Stage 3 reflection is a pre-generation self-check over the observations, shortlist, plan, and draft prompt.
- Call the image-generation tool exactly once after reflection with the final revised prompt/reference list."""
    raise AssertionError(f"unhandled pipe generation mode: {mode}")


def build_strategy_prompt(
    base_prompt: str,
    strategy_name: str,
    harness_name: str,
    pipe_generation_mode: str | None = None,
) -> str:
    try:
        strategy = _STRATEGIES[strategy_name]
    except KeyError as exc:
        known = ", ".join(known_strategy_names())
        raise ValueError(f"unknown agent strategy {strategy_name!r}; known strategies: {known}") from exc

    generation_instructions = ""
    if strategy.name == "pipe":
        mode = parse_pipe_generation_mode(pipe_generation_mode)
        generation_instructions = f"\n\n{_pipe_generation_instructions(mode)}"

    return (
        f"{base_prompt.rstrip()}\n\n"
        f"Agent strategy: {strategy.name} ({strategy.title})\n"
        f"Applies to harness: {harness_name}\n\n"
        f"{_COMMON_INSTRUCTIONS}\n\n"
        f"{strategy.instructions}{generation_instructions}\n"
    )
