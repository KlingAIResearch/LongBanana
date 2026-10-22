"""Retained direct visual Judge prompt, resize, retry, and answer rules."""
import json
import re
import time
from PIL import Image

MAX_IMAGE_PX = 1024
INVALID_RETRIES = 10
CAPTURE_USAGE = True
PASS_ANSWERS = {"match", "correct", "pass"}
FAIL_ANSWERS = {"mismatch_or_missing", "incorrect", "fail"}
ALL_ANSWERS = PASS_ANSWERS | FAIL_ANSWERS | {"uncertain"}
_ANSWER_RE = re.compile(r'"answer"\s*:\s*"([A-Za-z_]+)"')

RUBRIC = {
  "system": "",
  "rubric_rules": [
    {
      "id": "R1_evidence_only",
      "text": "严格基于附图中实际可见的证据；看不清或有歧义就选 uncertain"
    },
    {
      "id": "R2_no_extratextual",
      "text": "忽略画面外的上下文、标题文案、联想"
    },
    {
      "id": "R3_attach_order_default",
      "when": "not_global_check",
      "text": "附图顺序：第 1 张为目标图（待评候选图），其余为参考图。"
    },
    {
      "id": "R3_attach_order_global",
      "when": "global_check",
      "text": "本题是整图判题，只提供 1 张目标图（候选图），不提供任何参考图。"
    }
  ],
  "scoring_instructions": "",
  "output_format": "请以 JSON 形式输出：{\"answer\": \"<options 中的一个>\", \"reason\": \"<1-2 句为什么>\"}"
}

class Theta:
    def __init__(self):
        self.P = RUBRIC

    def render_prompt(self, t: dict) -> str:
        blocks: list[str] = []
        system = (self.P.get("system") or "").strip()
        if system:
            blocks.append(system)
        blocks.append(f"场景上下文：\n{t['scene']}")
        blocks.append(f"你需要判断的问题：\n{t['question']}")
        blocks.append(f"判题说明：\n{t['guide']}")
        blocks.append(
            f"可选答案（严格从中选一个）：\n"
            f"{json.dumps(t['options'], ensure_ascii=False)}"
        )
        blocks.append(
            f"每个选项的含义：\n"
            f"{json.dumps(t['option_desc'], ensure_ascii=False)}"
        )
        rubric_lines = ["判题要求："]
        for r in self.P.get("rubric_rules", []) or []:
            if _rule_applies(r, t):
                rubric_lines.append(f"- {r['text']}")
        blocks.append("\n".join(rubric_lines))
        scoring = (self.P.get("scoring_instructions") or "").strip()
        if scoring:
            blocks.append(scoring)
        blocks.append(self.P.get("output_format", ""))
        return "\n\n".join(blocks)

def _rule_applies(rule: dict, t: dict) -> bool:
    when = rule.get("when")
    if not when:
        return True
    tt = t.get("task_type", "")
    if when == "global_check":
        return tt == "global_check"
    if when == "not_global_check":
        return tt != "global_check"
    if when.startswith("task_type:"):
        return tt == when.split(":", 1)[1]
    return True

def ensure_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    if max(image.size) <= max_size:
        return image
    resized = image.copy()
    resized.thumbnail((max_size, max_size), Image.LANCZOS)
    return resized

def _repair_json(s: str) -> str:
    stack = []
    in_str = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            if ch == chr(92):
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                stack.append("}")
            elif ch == "[":
                stack.append("]")
            elif ch in "]}":
                if stack and stack[-1] == ch:
                    stack.pop()
        i += 1
    return s + "".join(reversed(stack))

def parse_json_markdown(json_output: str) -> str:
    m = re.search(r"```json\s*(.*?)```", json_output, re.DOTALL)
    if m:
        return m.group(1).strip()

    m = re.search(r"```\s*([\[\{].*?)```", json_output, re.DOTALL)
    if m:
        return m.group(1).strip()

    m = re.search(r"(\{.*\})", json_output, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        candidate = _repair_json(candidate)
        return candidate

    m = re.search(r"(\[.*\])", json_output, re.DOTALL)
    if m:
        return m.group(1).strip()

    return json_output.strip()

def build_prompt(t, theta):
    tt = {"task_type":t["category"],"case_uid":t["case_id"],"case_name":t["case_id"],
          "split":"","priority":"","scene":t["scene"],"question":t["question"],
          "guide":t["guide"],"options":t["options"],"option_desc":t["option_desc"],
          "refs":t["refs"],"n_refs_missing":0}
    return theta.render_prompt(tt)

def judge_one(client, t, theta):
    cp = t["candidate_path"]
    img_paths = [cp] if t["category"]=="global_check" else [cp, *t["refs"]]
    start = time.time()
    try:
        parts = []
        for p in img_paths:
            with Image.open(p) as im:
                im.load()
                small = ensure_image(im.convert("RGB"), MAX_IMAGE_PX)
                image_part = getattr(client, "image_part", None)
                parts.append(image_part(small) if callable(image_part) else pil_to_part(small))
    except Exception as e:
        return {"answer":"uncertain","is_pass":False,"is_uncertain":True,"is_invalid":True,
                "duration_s":round(time.time()-start,2),
                "error_msg":f"image_decode:{type(e).__name__}:{str(e)[:100]}","vlm_raw_head":""}
    contents = [build_prompt(t, theta), *parts]
    last_err, last_raw = "", ""
    history = []
    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
    }
    usage_model = ""
    def usage_fields():
        if not CAPTURE_USAGE:
            return {}
        return {**usage_totals, "usage_model": usage_model}
    for attempt in range(max(1, INVALID_RETRIES)):
        raw = None
        try:
            if CAPTURE_USAGE and hasattr(client, "generate_text_with_usage"):
                measured = client.generate_text_with_usage(
                    contents,
                    config={"max_output_tokens":8192},
                )
                raw = measured.get("text")
                usage_model = str(measured.get("model") or usage_model)
                for key in usage_totals:
                    usage_totals[key] += int(
                        (measured.get("usage") or {}).get(key, 0) or 0
                    )
            else:
                raw = client.generate_text(
                    contents,
                    config={"max_output_tokens":8192},
                )
        except Exception as e:
            last_err = f"call_exc:{type(e).__name__}:{str(e)[:100]}"
            history.append(f"a{attempt}:exc"); continue
        if raw is None: last_err="empty"; history.append(f"a{attempt}:empty"); continue
        last_raw = raw
        ans, aerr = "", ""
        try:
            ans = str(json.loads(parse_json_markdown(raw)).get("answer","")).strip()
        except:
            m = _ANSWER_RE.search(raw)
            if m and m.group(1) in ALL_ANSWERS: ans = m.group(1)
            else: aerr = "parse_fail"
        if ans in t["options"]:
            history.append(f"a{attempt}:ok")
            err = "" if attempt==0 else f"recovered_after_{attempt}_retries:{';'.join(history[:-1])}"
            return {"answer":ans,"is_pass":ans in PASS_ANSWERS,"is_uncertain":ans=="uncertain",
                    "is_invalid":False,"duration_s":round(time.time()-start,2),
                    "error_msg":err,"vlm_raw_head":raw[:200].replace("\n"," "),
                    **usage_fields()}
        last_err = aerr or f"oor:{ans[:40]}"
        history.append(f"a{attempt}:{('parse_fail' if aerr else 'oor')}")
    return {"answer":"uncertain","is_pass":False,"is_uncertain":True,"is_invalid":True,
            "duration_s":round(time.time()-start,2),
            "error_msg":f"invalid_after_{INVALID_RETRIES}:{last_err}|{';'.join(history)}",
            "vlm_raw_head":last_raw[:200].replace("\n"," ") if last_raw else "",
            **usage_fields()}

