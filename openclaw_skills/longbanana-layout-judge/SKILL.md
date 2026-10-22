---
name: longbanana-layout-judge
description: Use when a LongBanana judge task depends on spatial layout, relative position, overlap, ordering, alignment, or size relationships.
---

# LongBanana Layout Judge

Use this skill only as the `layout-judge` subagent.

Inspect the attached candidate and reference images directly. Check spatial
relations such as left/right, above/below, inside/outside, overlap, ordering,
alignment, relative size, and whether entities preserve the requested layout.

Return one JSON object and no `<answer>` block:

```json
{
  "agent": "layout-judge",
  "needed": true,
  "confidence": "high",
  "layout_checks": [{"relation": "A left of B", "result": "satisfied|violated|uncertain", "evidence": "..."}],
  "answer_relevance": "how layout evidence affects the task options",
  "evidence": ["visible layout evidence only"],
  "limitations": []
}
```
