---
name: longbanana-identity-judge
description: Use when a LongBanana judge task depends on matching reference identity, distinctive visual features, clothing, color, shape, texture, or entity attributes.
---

# LongBanana Identity Judge

Use this skill only as the `identity-judge` subagent.

Inspect the attached candidate and reference images directly. Compare visible
identity and feature cues between candidate and references: color, clothing,
shape, material, markings, pose-relevant attributes, and distinctive parts.

Return one JSON object and no `<answer>` block:

```json
{
  "agent": "identity-judge",
  "needed": true,
  "confidence": "high",
  "matched_features": ["visible matching feature"],
  "missing_or_changed_features": ["visible mismatch or missing feature"],
  "answer_relevance": "how identity/feature evidence affects the task options",
  "evidence": ["visible identity evidence only"],
  "limitations": []
}
```
