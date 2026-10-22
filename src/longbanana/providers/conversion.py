"""CC Switch-inspired native Gemini conversion (see NOTICE).

Deliberately retains JSON Schema and opaque Gemini call parts. Never fabricates
thought signatures. Stream envelopes are generated after buffered upstream replies.
"""
import copy
import json
import re
import threading
import time
import uuid
from collections import OrderedDict


def uid(prefix):
    return prefix + uuid.uuid4().hex


class Shadow:
    def __init__(self, limit=10000, ttl=7200):
        self.data = OrderedDict()
        self.lock = threading.Lock()
        self.limit, self.ttl = limit, ttl

    def put(self, route, key, value):
        with self.lock:
            self.data[(route, key)] = (time.monotonic(), copy.deepcopy(value))
            while len(self.data) > self.limit:
                self.data.popitem(last=False)

    def get(self, route, key):
        with self.lock:
            row = self.data.get((route, key))
            if row is None or time.monotonic() - row[0] > self.ttl:
                raise ValueError("Missing/expired conversation replay; restart this session")
            self.data[(route, key)] = (time.monotonic(), row[1])
            self.data.move_to_end((route, key))
            return copy.deepcopy(row[1])

    def history(self, route, key):
        chunks, seen = [], set()
        while key:
            if key in seen:
                raise ValueError("Invalid cyclic response history")
            seen.add(key)
            row = self.get(route, key)
            chunks.append(row["contents"])
            key = row.get("parent")
        return [content for chunk in reversed(chunks) for content in chunk]


def clean_schema(value):
    if isinstance(value, list):
        return [clean_schema(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_schema(v) for k, v in value.items() if k not in ("$schema", "$id")}
    return value


class Converter:
    def __init__(self, route, shadow):
        self.route, self.shadow = route, shadow
        self.tools = {}
        self.calls = {}
        self.previous_length = 0

    def tool_name(self, name, namespace=None, custom=False):
        full = (namespace + "." if namespace else "") + name
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", full)
        if safe in self.tools and self.tools[safe] != (name, namespace, custom):
            raise ValueError("Tool name collision after Gemini normalization")
        self.tools[safe] = (name, namespace, custom)
        return safe

    def declarations(self, tools, proto, namespace=None):
        declarations = []
        for tool in tools:
            kind = tool.get("type", "function")
            if kind == "namespace":
                declarations.extend(self.declarations(tool.get("tools", []), proto, tool["name"]))
                continue
            if kind not in ("function", "custom"):
                raise ValueError("Unsupported tool type: " + kind)
            name = self.tool_name(tool["name"], namespace, kind == "custom")
            schema = tool.get("input_schema", {}) if proto == "anthropic" else tool.get("parameters", {})
            if kind == "custom":
                schema = {"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]}
            schema = clean_schema(schema)
            schema.setdefault("type", "object")
            if schema["type"] == "object":
                schema.setdefault("properties", {})
            declarations.append({"name": name, "description": tool.get("description", ""), "parametersJsonSchema": schema})
        return declarations

    def media(self, block):
        kind = block.get("type")
        if kind in ("text", "input_text", "output_text"):
            return {"text": block.get("text", "")}
        if kind in ("image", "document"):
            source = block.get("source", {})
            if source.get("type") != "base64":
                raise ValueError("Use inline base64 media; remote URL fetching is disabled")
            return {"inlineData": {"mimeType": source.get("media_type", "image/png"), "data": source["data"]}}
        if kind == "input_image":
            url = block.get("image_url", "")
            if not isinstance(url, str) or not url.startswith("data:") or ";base64," not in url:
                raise ValueError("Responses image input requires a base64 data URL")
            header, data = url.split(",", 1)
            return {"inlineData": {"mimeType": header[5:].split(";")[0], "data": data}}
        raise ValueError("Unsupported content block: " + str(kind))

    def call_part(self, call_id, name, arguments, namespace=None, custom=False):
        safe = self.tool_name(name, namespace, custom)
        self.calls[call_id] = safe
        if call_id.startswith("lb_call_"):
            part = self.shadow.get(self.route, call_id)
            if part["functionCall"]["name"] != safe:
                raise ValueError("Replayed tool name differs from original call")
            return part
        args = {"input": arguments} if custom else arguments
        if isinstance(args, str):
            args = json.loads(args)
        return {"functionCall": {"name": safe, "args": args, "id": call_id}}

    def result_parts(self, call_id, value, error=False):
        original = self.shadow.get(self.route, call_id) if call_id.startswith("lb_call_") else None
        name = original["functionCall"]["name"] if original else self.calls.get(call_id)
        if not name:
            raise ValueError("Unknown tool result call ID")
        media, texts = [], []
        if isinstance(value, list):
            for block in value:
                part = self.media(block)
                if "inlineData" in part:
                    media.append(part)
                else:
                    texts.append(part["text"])
            value = "\n".join(texts)
        result = {"name": name, "response": {"error" if error else "result": value}}
        upstream_id = original["functionCall"].get("id") if original else call_id
        if upstream_id:
            result["id"] = upstream_id
        if media:
            result["parts"] = media
        return [{"functionResponse": result}]

    def request(self, body, proto):
        payload, contents, system = {}, [], []
        declarations = self.declarations(body.get("tools", []), proto)
        if declarations:
            payload["tools"] = [{"functionDeclarations": declarations}]
        def append(role, parts):
            if not parts:
                return
            role = "model" if role == "assistant" else "user"
            # Gemini 3.x must not receive functionResponse mixed with ordinary
            # user text in one content. Preserve both in separate user contents.
            groups = []
            for part in parts:
                category = role == "user" and "functionResponse" in part
                if groups and groups[-1][0] == category:
                    groups[-1][1].append(part)
                else:
                    groups.append((category, [part]))
            for category, group in groups:
                previous_category = contents and "functionResponse" in contents[-1]["parts"][0]
                if contents and contents[-1]["role"] == role and (role == "model" or previous_category == category):
                    contents[-1]["parts"].extend(group)
                else:
                    contents.append({"role": role, "parts": group})
        if proto == "anthropic":
            sys_content = body.get("system", [])
            system.extend([{"text": sys_content}] if isinstance(sys_content, str) else [self.media(x) for x in sys_content])
            for msg in body.get("messages", []):
                blocks = msg.get("content", [])
                if isinstance(blocks, str):
                    blocks = [{"type": "text", "text": blocks}]
                parts = []
                for block in blocks:
                    kind = block.get("type")
                    if kind == "tool_use":
                        parts.append(self.call_part(block["id"], block["name"], block["input"]))
                    elif kind == "tool_result":
                        parts.extend(self.result_parts(block["tool_use_id"], block.get("content", ""), block.get("is_error", False)))
                    elif kind not in ("thinking", "redacted_thinking"):
                        parts.append(self.media(block))
                if msg["role"] == "system":
                    system.extend(parts)
                else:
                    append(msg["role"], parts)
        else:
            inputs = body.get("input", [])
            if isinstance(inputs, str):
                inputs = [{"role": "user", "content": inputs}]
            if body.get("previous_response_id"):
                contents = self.shadow.history(self.route, body["previous_response_id"])
                self.previous_length = len(contents)
            if body.get("instructions"):
                system.append({"text": body["instructions"]})
            for item in inputs:
                kind = item.get("type", "message")
                if kind in ("function_call", "custom_tool_call"):
                    append("assistant", [self.call_part(item["call_id"], item["name"], item.get("input", "") if kind == "custom_tool_call" else item.get("arguments", "{}"), item.get("namespace"), kind == "custom_tool_call")])
                elif kind in ("function_call_output", "custom_tool_call_output"):
                    append("user", self.result_parts(item["call_id"], item.get("output", "")))
                elif kind == "reasoning":
                    continue
                elif kind == "message":
                    value = item.get("content", [])
                    parts = [{"text": value}] if isinstance(value, str) else [self.media(x) for x in value]
                    if item.get("role") in ("system", "developer"):
                        system.extend(parts)
                    else:
                        append(item.get("role", "user"), parts)
                else:
                    raise ValueError("Unsupported Responses input item: " + kind)
        payload["contents"] = contents
        if system:
            payload["systemInstruction"] = {"parts": system}
        config = {}
        for src, dst in (("max_tokens", "maxOutputTokens"), ("max_output_tokens", "maxOutputTokens"), ("temperature", "temperature"), ("top_p", "topP"), ("stop_sequences", "stopSequences")):
            if src in body:
                config[dst] = body[src]
        if config:
            payload["generationConfig"] = config
        choice = body.get("tool_choice")
        if choice:
            mode = choice.get("type") if isinstance(choice, dict) else choice
            mapped = {"auto": "AUTO", "none": "NONE", "any": "ANY", "required": "ANY", "tool": "ANY", "function": "ANY"}
            if mode not in mapped:
                raise ValueError("Unsupported tool_choice")
            fc = {"mode": mapped[mode]}
            if mode in ("tool", "function"):
                fc["allowedFunctionNames"] = [self.tool_name(choice["name"])]
            payload["toolConfig"] = {"functionCallingConfig": fc}
        return payload

    def response(self, upstream, body, proto, payload):
        candidates = upstream.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned no candidates (possibly blocked)")
        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        output = []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if text:
            output.append({"type": "text", "text": text} if proto == "anthropic" else {"type": "message", "role": "assistant", "id": uid("msg_"), "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]})
        for part in parts:
            if "functionCall" not in part:
                continue
            call = part["functionCall"]
            if call["name"] not in self.tools:
                raise ValueError("Gemini requested an undeclared tool")
            name, namespace, custom = self.tools[call["name"]]
            call_id = uid("lb_call_")
            self.shadow.put(self.route, call_id, part)
            args = call.get("args", {})
            if proto == "anthropic":
                output.append({"type": "tool_use", "id": call_id, "name": name, "input": args})
            else:
                item = {"type": "custom_tool_call" if custom else "function_call", "id": uid("fc_"), "call_id": call_id, "name": name, "status": "completed"}
                item["input" if custom else "arguments"] = args.get("input", "") if custom else json.dumps(args)
                if namespace:
                    item["namespace"] = namespace
                output.append(item)
        if not output:
            raise ValueError("Gemini returned no visible text or tool calls; finish=" + str(candidate.get("finishReason")) + "; part_types=" + str([list(p.keys()) for p in parts]))
        usage = upstream.get("usageMetadata", {})
        input_n, output_n = usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        if proto == "anthropic":
            reason = "tool_use" if any(x["type"] == "tool_use" for x in output) else "end_turn"
            if candidate.get("finishReason") == "MAX_TOKENS":
                reason = "max_tokens"
            return {"id": uid("msg_"), "type": "message", "role": "assistant", "model": body["model"], "content": output, "stop_reason": reason, "stop_sequence": None, "usage": {"input_tokens": input_n, "output_tokens": output_n}}
        response_id = uid("resp_")
        if body.get("store", True):
            self.shadow.put(self.route, response_id, {"parent": body.get("previous_response_id"), "contents": payload["contents"][self.previous_length:] + [{"role": "model", "parts": parts}]})
        status = "incomplete" if candidate.get("finishReason") == "MAX_TOKENS" else "completed"
        return {"id": response_id, "object": "response", "created_at": int(time.time()), "model": body["model"], "status": status, "output": output, "error": None, "incomplete_details": {"reason": "max_output_tokens"} if status == "incomplete" else None, "usage": {"input_tokens": input_n, "output_tokens": output_n, "total_tokens": input_n + output_n, "input_tokens_details": {"cached_tokens": usage.get("cachedContentTokenCount", 0)}, "output_tokens_details": {"reasoning_tokens": usage.get("thoughtsTokenCount", 0)}}}


def events(response, proto):
    if proto == "anthropic":
        yield "message_start", {"type": "message_start", "message": {**response, "content": [], "stop_reason": None, "usage": {**response["usage"], "output_tokens": 0}}}
        for index, block in enumerate(response["content"]):
            initial = {**block, "text": ""} if block["type"] == "text" else {**block, "input": {}}
            yield "content_block_start", {"type": "content_block_start", "index": index, "content_block": initial}
            delta = {"type": "text_delta", "text": block["text"]} if block["type"] == "text" else {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
            yield "content_block_delta", {"type": "content_block_delta", "index": index, "delta": delta}
            yield "content_block_stop", {"type": "content_block_stop", "index": index}
        yield "message_delta", {"type": "message_delta", "delta": {"stop_reason": response["stop_reason"], "stop_sequence": None}, "usage": response["usage"]}
        yield "message_stop", {"type": "message_stop"}
    else:
        yield "response.created", {"type": "response.created", "response": {**response, "status": "in_progress", "output": [], "usage": None}}
        for index, item in enumerate(response["output"]):
            initial = {**item, "status": "in_progress"}
            if item["type"] == "message":
                initial["content"] = []
            else:
                initial["input" if item["type"] == "custom_tool_call" else "arguments"] = ""
            yield "response.output_item.added", {"type": "response.output_item.added", "output_index": index, "item": initial}
            if item["type"] == "message":
                part = item["content"][0]
                base = {"item_id": item["id"], "output_index": index, "content_index": 0}
                yield "response.content_part.added", {"type": "response.content_part.added", **base, "part": {**part, "text": ""}}
                yield "response.output_text.delta", {"type": "response.output_text.delta", **base, "delta": part["text"]}
                yield "response.output_text.done", {"type": "response.output_text.done", **base, "text": part["text"]}
                yield "response.content_part.done", {"type": "response.content_part.done", **base, "part": part}
            else:
                custom = item["type"] == "custom_tool_call"
                stem = "response.custom_tool_call_input" if custom else "response.function_call_arguments"
                field = "input" if custom else "arguments"
                yield stem + ".delta", {"type": stem + ".delta", "item_id": item["id"], "output_index": index, "delta": item[field]}
                yield stem + ".done", {"type": stem + ".done", "item_id": item["id"], "output_index": index, field: item[field]}
            yield "response.output_item.done", {"type": "response.output_item.done", "output_index": index, "item": item}
        event = "response.completed" if response["status"] == "completed" else "response.incomplete"
        yield event, {"type": event, "response": response}
