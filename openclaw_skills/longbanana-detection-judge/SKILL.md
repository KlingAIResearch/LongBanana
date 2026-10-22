---
name: longbanana-detection-judge
description: Use when a LongBanana judge task depends on object detection, entity presence, object counting, missing objects, or extra objects.
---

# LongBanana Detection Judge

Use this skill only as the `detector-judge` subagent.

Inspect the attached candidate and reference images directly. Count only objects
that are visibly present. If a target object is partially visible or ambiguous,
state that uncertainty instead of forcing a count.

Return one JSON object and no `<answer>` block:

```json
{
  "agent": "detector-judge",
  "needed": true,
  "confidence": "high",
  "objects": [{"image": "candidate|reference", "label": "...", "count": 1, "location": "brief visible location"}],
  "counts": {"target object": 1},
  "answer_relevance": "how object presence or count affects the task options",
  "evidence": ["visible detection/counting evidence only"],
  "limitations": []
}
```
