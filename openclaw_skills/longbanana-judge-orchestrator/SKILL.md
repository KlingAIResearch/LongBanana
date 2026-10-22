---
name: longbanana-judge-orchestrator
description: Use when judging LongBanana image-generation results and delegating OCR, detection, layout, or identity evidence checks to specialized subagents.
---

# LongBanana Judge Orchestrator

Use this skill for the main OpenClaw judge only.

Spawn specialized subagents with `sessions_spawn` when their evidence can affect
the final LongBanana judgment. Always include the candidate image path,
reference image paths, task question, guide, options, and the exact evidence
request in the child task.

- Use `agentId: "ocr-judge"` for readable text, labels, signs, numbers, and UI text.
- Use `agentId: "detector-judge"` for object presence, missing or extra objects, and counts.
- Use `agentId: "layout-judge"` for left/right/above/below, overlap, ordering, and relative size.
- Use `agentId: "identity-judge"` for reference identity, clothing, color, shape, and distinctive features.

Do not generate, edit, copy, save, or delete images. Merge child evidence into
the final answer only when it is grounded in visible image evidence.

Final output must be exactly one `<answer>` block. Keep the normal `answer`,
`reason`, and `evidence` fields, and include `subagent_evidence` with keys
`ocr`, `detection`, `layout`, and `identity`.
