"""Bound image transport on HTTP 413 without dropping evidence or changing files."""
import base64
import copy
import io


def compress_responses_images(payload, quality=90):
    """Opt-in native Responses image encoding only; never resize or rewrite history.

    Only typed input_image blocks in messages/tool outputs are eligible. Text,
    schemas, opaque reasoning, external URLs and unsupported image formats stay
    untouched. Original files are never read or written by this function.
    """
    from PIL import Image, ImageOps

    if quality != 90:
        raise ValueError("Native image transport supports only JPEG quality 90")
    result = copy.deepcopy(payload)
    stats = {"images": 0, "changed": 0, "before_base64_bytes": 0,
             "after_base64_bytes": 0, "quality": quality, "resize": False}

    def content(parts):
        if not isinstance(parts, list):
            return
        for part in parts:
            if not isinstance(part, dict) or part.get("type") != "input_image":
                continue
            url = part.get("image_url")
            if not isinstance(url, str) or not url.startswith((
                    "data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")):
                continue
            original = url.split(",", 1)[1]
            stats["images"] += 1
            stats["before_base64_bytes"] += len(original)
            data = original
            try:
                with Image.open(io.BytesIO(base64.b64decode(original, validate=True))) as source:
                    # Do not flatten transparency, discard animation or silently
                    # reinterpret a non-image as an image.
                    if (source.format not in ("PNG", "JPEG", "WEBP") or
                            getattr(source, "n_frames", 1) != 1 or
                            "A" in source.getbands() or "transparency" in source.info):
                        stats["after_base64_bytes"] += len(original)
                        continue
                    image = ImageOps.exif_transpose(source).convert("RGB")
                    encoded = io.BytesIO()
                    image.save(encoded, format="JPEG", quality=quality, optimize=True)
                candidate = base64.b64encode(encoded.getvalue()).decode("ascii")
                if len(candidate) < len(original):
                    data = candidate
                    part["image_url"] = "data:image/jpeg;base64," + data
                    stats["changed"] += 1
            except (ValueError, OSError):
                # Preserve provider validation semantics for malformed media.
                pass
            stats["after_base64_bytes"] += len(data)

    items = result.get("input")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "function_call_output":
                content(item.get("output"))
            elif item.get("type") == "message" or ("role" in item and "type" not in item):
                content(item.get("content"))
    return result, stats


def compress_images(payload, max_edge=1024, quality=85):
    from PIL import Image, ImageOps

    result = copy.deepcopy(payload)
    stats = {"images": 0, "changed": 0, "before_base64_bytes": 0, "after_base64_bytes": 0,
             "max_edge": max_edge, "quality": quality}

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            inline = value.get("inlineData")
            if isinstance(inline, dict) and inline.get("mimeType", "").startswith("image/"):
                original = inline["data"]
                with Image.open(io.BytesIO(base64.b64decode(original, validate=True))) as source:
                    image = ImageOps.exif_transpose(source)
                    # Thumbnail keeps aspect ratio and never upscales or crops.
                    image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
                    if "A" in image.getbands() or image.mode == "P":
                        rgba = image.convert("RGBA")
                        rgb = Image.new("RGB", rgba.size, "white")
                        rgb.paste(rgba, mask=rgba.getchannel("A"))
                    else:
                        rgb = image.convert("RGB")
                    encoded = io.BytesIO()
                    rgb.save(encoded, format="JPEG", quality=quality, optimize=True)
                data = base64.b64encode(encoded.getvalue()).decode("ascii")
                stats["images"] += 1
                stats["before_base64_bytes"] += len(original)
                if len(data) < len(original):
                    inline["data"], inline["mimeType"] = data, "image/jpeg"
                    stats["changed"] += 1
                stats["after_base64_bytes"] += len(inline["data"])
            for key, child in value.items():
                if key != "inlineData":
                    visit(child)

    visit(result)
    return result, stats
