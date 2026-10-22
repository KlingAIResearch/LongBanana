# Gemini Image-Gen — Reference for Agents (Codex / Claude Code)

Optional reference for the image-generation tool: its interface, official
capabilities, and official prompting guidance. Reference selection, prompt
composition, and iteration remain your decisions.

This follows the legacy Gemini reference's six-section structure and guidance,
adapted to the native sandbox. The current pipeline uses `gemini-3.1-flash-image`.
Official sources checked 2026-10-13: Google's
[image-generation guide](https://ai.google.dev/gemini-api/docs/image-generation).

## 1. The call you make

Codex and Claude Code use the same `generate_image` MCP tool:

```json
{"prompt":"Combine the desired elements", "reference_images":["/refs/R01__reference.png"], "output_dir":"/output"}
```

`prompt` is required. `reference_images` defaults to `[]`; an empty list enables
text-only generation. `output_dir` defaults to `/output`. The supervisor supplies
model configuration and credentials. One call returns one image; call again with
an updated prompt or a saved image for another edit.

## 2. Reference images

Google documents up to **14 reference images** for Gemini 3 image models; for
Gemini 3.1 Flash Image, this includes up to **10 object images** and **4 character
images** for fidelity and consistency.
See the [official reference-image section](https://ai.google.dev/gemini-api/docs/image-generation#use_up_to_14_reference_images).

Pass absolute paths. The adapter sends references in supplied order as inline
image parts, without object/character tagging or automatic selection. Transport
copies are resized to a maximum long side of 1024 pixels, preserving aspect ratio;
read-only files under `/refs` remain unchanged. A background or previous output
counts as a supplied image. The JSON Schema adds no reference-count cap.

## 3. Prompt (official guidance)

The legacy reference's central recommendation remains: describe a coherent
scene rather than a collection of keywords. Google's guide favors a descriptive
paragraph that communicates the intended image.

This is guidance, not a mandatory prompt template or iteration policy.
See [Google's prompting guidance](https://ai.google.dev/gemini-api/docs/image-generation).

## 4. Output

Google states that generated images include a SynthID watermark.
See [official limitations](https://ai.google.dev/gemini-api/docs/image-generation#limitations).

The tool saves the full-resolution image and returns its absolute path with a
JPEG preview. The preview preserves aspect ratio and has a maximum long side of
1024 pixels; it does not replace the original. A returned path can be supplied
in a later `reference_images` list. Read images with Codex `view_image` or Claude
Code `Read`; no separate reference-viewing MCP tool is provided.

## 5. What the tool does not forward

Only the three arguments above are exposed. Thinking controls, output size,
aspect-ratio API settings, search tools, watermark controls, and other generation
settings are not tool arguments. Adding unsupported keys does not configure those
features. Model/API capabilities do not imply that every option is exposed here.

## 6. Failure symptoms

| Symptom | Mechanical meaning |
| --- | --- |
| Unreadable reference path | The file cannot be read inside the sandbox. |
| API or image-bridge HTTP error | The configured service returned a non-success response. |
| Response contains no image | No usable generated image was returned. |
| Network error or timeout | The call did not finish locally; upstream completion may be unknown. |

These describe tool behavior, not a required recovery strategy. A timeout is not
proof that upstream generation never completed.
