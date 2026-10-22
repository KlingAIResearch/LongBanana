import copy
import json
from .conversion import uid

def media(part, responses=False, assistant=False):
    if "text" in part:
        return {"type": "output_text" if assistant else "input_text", "text": part["text"]} if responses else {"type": "text", "text": part["text"]}
    if "inlineData" in part:
        inline = part["inlineData"]
        if not inline["mimeType"].startswith("image/"):
            raise ValueError("Only inline images are supported by this bridge")
        url = "data:" + inline["mimeType"] + ";base64," + inline["data"]
        return {"type": "input_image", "image_url": url} if responses else {"type": "image_url", "image_url": {"url": url}}
    raise ValueError("Unsupported canonical media")


def declarations(payload):
    return [function for group in payload.get("tools", []) for function in group["functionDeclarations"]]


def choice(payload, responses):
    config = payload.get("toolConfig", {}).get("functionCallingConfig")
    if not config:
        return None
    names = config.get("allowedFunctionNames")
    if names:
        return {"type": "function", "name": names[0]} if responses else {"type": "function", "function": {"name": names[0]}}
    return {"AUTO": "auto", "NONE": "none", "ANY": "required"}[config["mode"]]


def to_chat(payload, model):
    messages = []
    system = payload.get("systemInstruction", {}).get("parts", [])
    if system:
        if any("text" not in part for part in system):
            raise ValueError("System media is unsupported")
        messages.append({"role": "system", "content": "\n".join(part["text"] for part in system)})
    for content in payload["contents"]:
        parts = content["parts"]
        if content["role"] == "model":
            message = {"role": "assistant", "content": "".join(part.get("text", "") for part in parts) or None}
            calls = [part["functionCall"] for part in parts if "functionCall" in part]
            if calls:
                message["tool_calls"] = [{"id": call["id"], "type": "function",
                    "function": {"name": call["name"], "arguments": json.dumps(call.get("args", {}))}}
                    for call in calls]
            messages.append(message)
        else:
            normal = []
            for part in parts:
                if "functionResponse" not in part:
                    normal.append(media(part))
                    continue
                result = part["functionResponse"]
                messages.append({"role": "tool", "tool_call_id": result["id"],
                    "content": json.dumps(result["response"], ensure_ascii=False)})
                normal.extend(media(image) for image in result.get("parts", []))
            if normal:
                messages.append({"role": "user", "content": normal})
    body = {"model": model, "messages": messages, "stream": False}
    funcs = declarations(payload)
    if funcs:
        body["tools"] = [{"type": "function", "function": {"name": f["name"],
            "description": f.get("description", ""), "parameters": f["parametersJsonSchema"]}} for f in funcs]
    tool_choice = choice(payload, False)
    if tool_choice:
        body["tool_choice"] = tool_choice
    config = payload.get("generationConfig", {})
    for source, target in (("maxOutputTokens", "max_completion_tokens"), ("temperature", "temperature"), ("topP", "top_p"), ("stopSequences", "stop")):
        if source in config:
            body[target] = config[source]
    return body


def to_responses(payload, model):
    items = []
    for content in payload["contents"]:
        parts = content["parts"]
        if content["role"] == "model":
            seen = set()
            for part in parts:
                for original in part.get("_responses_reasoning", []):
                    if original["id"] not in seen:
                        items.append(copy.deepcopy(original))
                        seen.add(original["id"])
            text = [media(part, True, True) for part in parts if "text" in part]
            if text:
                items.append({"type": "message", "role": "assistant", "content": text})
            for part in parts:
                if "functionCall" in part:
                    call = part["functionCall"]
                    items.append(copy.deepcopy(part.get("_responses_call")) or {
                        "type": "function_call", "call_id": call["id"], "name": call["name"],
                        "arguments": json.dumps(call.get("args", {}))})
        else:
            normal = []
            for part in parts:
                if "functionResponse" not in part:
                    normal.append(media(part, True))
                    continue
                result = part["functionResponse"]
                value = json.dumps(result["response"], ensure_ascii=False)
                output = [{"type": "input_text", "text": value}] + [media(image, True) for image in result.get("parts", [])]
                items.append({"type": "function_call_output", "call_id": result["id"],
                              "output": output if len(output) > 1 else value})
            if normal:
                items.append({"type": "message", "role": "user", "content": normal})
    body = {"model": model, "input": items, "stream": False,
            "store": False, "include": ["reasoning.encrypted_content"]}
    system = payload.get("systemInstruction", {}).get("parts", [])
    if system:
        if any("text" not in part for part in system):
            raise ValueError("System media is unsupported")
        body["instructions"] = "\n".join(part["text"] for part in system)
    funcs = declarations(payload)
    if funcs:
        body["tools"] = [{"type": "function", "name": f["name"], "description": f.get("description", ""),
                          "parameters": f["parametersJsonSchema"], "strict": False} for f in funcs]
    tool_choice = choice(payload, True)
    if tool_choice:
        body["tool_choice"] = tool_choice
    config = payload.get("generationConfig", {})
    for source, target in (("maxOutputTokens", "max_output_tokens"), ("temperature", "temperature"), ("topP", "top_p")):
        if source in config:
            body[target] = config[source]
    return body


def canonical_response(body, responses):
    parts = []
    if responses:
        reasoning = [item for item in body.get("output", []) if item.get("type") == "reasoning"]
        for item in body.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        parts.append({"text": content["text"], "_responses_reasoning": reasoning})
                    elif content.get("type") == "refusal":
                        parts.append({"text": content["refusal"]})
            elif item.get("type") == "function_call":
                parts.append({"functionCall": {"name": item["name"], "id": item["call_id"],
                    "args": json.loads(item["arguments"])}, "_responses_call": copy.deepcopy(item),
                    "_responses_reasoning": reasoning})
        usage = body.get("usage") or {}
        inputs, outputs = usage.get("input_tokens") or 0, usage.get("output_tokens") or 0
        cached = (usage.get("input_tokens_details") or {}).get("cached_tokens") or 0
        thoughts = (usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0
        finish = "MAX_TOKENS" if body.get("status") == "incomplete" else "STOP"
    else:
        candidate = body["choices"][0]
        message = candidate["message"]
        if message.get("content"):
            parts.append({"text": message["content"]})
        for call in message.get("tool_calls") or []:
            parts.append({"functionCall": {"name": call["function"]["name"], "id": call["id"],
                                          "args": json.loads(call["function"]["arguments"])}})
        usage = body.get("usage") or {}
        inputs, outputs = usage.get("prompt_tokens") or 0, usage.get("completion_tokens") or 0
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
        thoughts = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        finish = "MAX_TOKENS" if candidate.get("finish_reason") == "length" else "STOP"
    return {"candidates": [{"content": {"parts": parts}, "finishReason": finish}],
            "usageMetadata": {"promptTokenCount": inputs, "candidatesTokenCount": outputs - thoughts,
                              "thoughtsTokenCount": thoughts, "cachedContentTokenCount": cached}}


