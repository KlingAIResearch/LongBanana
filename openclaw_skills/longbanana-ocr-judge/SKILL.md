---
name: longbanana-ocr-judge
description: Use when a LongBanana judge task depends on readable text, signs, labels, UI text, numbers, logos, or visible written content.
---

# LongBanana OCR Judge

Use this skill only as the `ocr-judge` subagent.

Inspect the attached candidate and reference images directly. Report only
readable text that is visible enough to support or weaken the main judge's
answer. Do not infer text from filenames, task text, or expected labels.

Return one JSON object and no `<answer>` block:

```json
{
  "agent": "ocr-judge",
  "needed": true,
  "confidence": "high",
  "text_blocks": [{"image": "candidate|reference", "text": "...", "location": "brief visible location"}],
  "answer_relevance": "how the visible text affects the task options",
  "evidence": ["visible OCR evidence only"],
  "limitations": []
}
```
