import { z } from "zod";
import { writeFile, mkdir, readFile } from "node:fs/promises";
import { join, resolve, isAbsolute } from "node:path";
import { homedir } from "node:os";
import sharp from "sharp";
import { EnvHttpProxyAgent, setGlobalDispatcher } from "undici";
// ---------------------------------------------------------------------------
// Proxy setup. Match the Python image backends: keep HTTP(S) proxy for
// Google/Azure/Ark egress on this host, but drop SOCKS/all_proxy entries that
// have caused broken TLS routing. Node fetch does not automatically use proxy
// env vars, so install undici's env-aware dispatcher explicitly.
// ---------------------------------------------------------------------------
for (const k of [
    "all_proxy", "ALL_PROXY", "socks_proxy", "SOCKS_PROXY",
]) {
    delete process.env[k];
}
process.env.NO_PROXY ??= "localhost,127.0.0.1";
process.env.no_proxy ??= process.env.NO_PROXY;
if (process.env.http_proxy || process.env.HTTP_PROXY ||
    process.env.https_proxy || process.env.HTTPS_PROXY) {
    setGlobalDispatcher(new EnvHttpProxyAgent());
}
// ---------------------------------------------------------------------------
// Logger (stderr, prefixed per-server)
// ---------------------------------------------------------------------------
export function makeLogger(name) {
    return (...args) => console.error(`[${name}]`, ...args);
}
const CONFIG_PATH = process.env.IMAGE_GEN_CONFIG ??
    resolve(join(process.env.HOME ?? homedir(), ".config", "openclaw-longbanana", "image_gen_config.json"));
let _configCache = null;
export async function loadConfig() {
    if (_configCache)
        return _configCache;
    const raw = await readFile(CONFIG_PATH, "utf-8");
    _configCache = JSON.parse(raw);
    return _configCache;
}
export function mimeForExt(path) {
    const lo = path.toLowerCase();
    if (lo.endsWith(".jpg") || lo.endsWith(".jpeg"))
        return "image/jpeg";
    if (lo.endsWith(".webp"))
        return "image/webp";
    if (lo.endsWith(".bmp"))
        return "image/bmp";
    if (lo.endsWith(".tif") || lo.endsWith(".tiff"))
        return "image/tiff";
    if (lo.endsWith(".gif"))
        return "image/gif";
    return "image/png";
}
// ---------------------------------------------------------------------------
// Reference-image preprocessor: cap long side before sending to any backend.
// Aligns with harness/image_gen/_resize.py on the Python router side. Keeps
// upload payloads bounded (30+ refs x 1-2MB each can saturate network egress
// and trips /images/edits write-timeout — observed 2026-04-23).
// Default MAX 1024 px; override via MAX_REF_LONG_SIDE env.
// ---------------------------------------------------------------------------
const _MAX_REF_LONG_SIDE = Number(process.env.MAX_REF_LONG_SIDE ?? "1024");
export async function resizeRefForSend(rawBytes, maxLongSide = _MAX_REF_LONG_SIDE) {
    const meta = await sharp(rawBytes).metadata();
    const longest = Math.max(meta.width ?? 0, meta.height ?? 0);
    const hasAlpha = meta.hasAlpha === true;
    // Always re-encode (consistent shape across backends); just skip resize
    // if source already fits.
    const needsResize = longest > maxLongSide;
    const pipeline = needsResize
        ? sharp(rawBytes).resize({
            width: maxLongSide,
            height: maxLongSide,
            fit: "inside",
            withoutEnlargement: true,
        })
        : sharp(rawBytes);
    if (hasAlpha) {
        const out = await pipeline.png({ compressionLevel: 9 }).toBuffer();
        return { bytes: out, mime: "image/png" };
    }
    const out = await pipeline.jpeg({ quality: 90 }).toBuffer();
    return { bytes: out, mime: "image/jpeg" };
}
export const DEFAULT_OUTPUT_DIR = process.env.IMAGE_OUTPUT_DIR ??
    join(homedir(), ".image-gen-mcp", "generated");
export async function saveImages(images, outputDir) {
    await mkdir(outputDir, { recursive: true });
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const paths = [];
    for (let i = 0; i < images.length; i++) {
        const ext = images[i].mimeType.includes("jpeg") ? "jpg" : "png";
        const filename = `img_${timestamp}_${i}.${ext}`;
        const filepath = join(outputDir, filename);
        await writeFile(filepath, Buffer.from(images[i].base64, "base64"));
        paths.push(filepath);
    }
    return paths;
}
// ---------------------------------------------------------------------------
// Shared view_reference_image tool — identical across backends.
// ---------------------------------------------------------------------------
const DATA_ROOT = process.env.LONGBANANA_DATA_ROOT ??
    process.cwd();
export function registerViewTool(server) {
    server.tool("view_reference_image", "Load a reference image from disk and return it as MCP image content so the agent's VLM can see it. Accepts either an absolute path or one relative to the dataset root.", {
        path: z.string().describe("Absolute path or dataset-relative path (e.g. LAC/LAC-001/case_001/refs/E01_foo.png)."),
    }, async ({ path }) => {
        try {
            const abs = isAbsolute(path) ? path : resolve(DATA_ROOT, path);
            const rawBytes = await readFile(abs);
            // Downsample large refs before handing to the VLM. Each full-
            // resolution png (~1-2 MB, ~2048 px side) costs ~1500 vision
            // tokens, and agents that eagerly view all 30+ refs can exceed
            // vision context limits. 768 px longest-side JPEG quality 85 keeps
            // enough detail for compositional reasoning at ~400-600
            // tokens/image and ~50-120 KB base64. Small sources pass
            // through unresized.
            const MAX_SIDE = Number(process.env.MCP_VIEW_MAX_SIDE ?? "768");
            const JPEG_Q = Number(process.env.MCP_VIEW_JPEG_QUALITY ?? "85");
            let outBytes;
            let outMime;
            const meta = await sharp(rawBytes).metadata();
            const needsResize = (meta.width ?? 0) > MAX_SIDE || (meta.height ?? 0) > MAX_SIDE;
            if (needsResize) {
                outBytes = await sharp(rawBytes)
                    .resize({ width: MAX_SIDE, height: MAX_SIDE, fit: "inside", withoutEnlargement: true })
                    .jpeg({ quality: JPEG_Q })
                    .toBuffer();
                outMime = "image/jpeg";
            }
            else {
                outBytes = rawBytes;
                outMime = mimeForExt(abs);
            }
            return {
                content: [
                    { type: "text",
                        text: `Loaded ${abs} (${rawBytes.length} bytes raw, served as ${outBytes.length} bytes ${outMime}${needsResize ? ` resized to fit ${MAX_SIDE}px` : ""})` },
                    { type: "image", data: outBytes.toString("base64"), mimeType: outMime },
                ],
            };
        }
        catch (err) {
            return {
                content: [{ type: "text",
                        text: `Error reading image at ${path}: ${err instanceof Error ? err.message : String(err)}` }],
                isError: true,
            };
        }
    });
}
// ---------------------------------------------------------------------------
// Render generate_image response payload shape (same across backends).
// ---------------------------------------------------------------------------
export function renderGenerateResponse(images, savedPaths, backendLabel) {
    const content = [];
    content.push({
        type: "text",
        text: `Generated ${images.length} image(s) via ${backendLabel}:`,
    });
    for (let i = 0; i < images.length; i++) {
        content.push({
            type: "image",
            data: images[i].base64,
            mimeType: images[i].mimeType,
        });
        let caption = `Image ${i + 1} saved to: ${savedPaths[i]}`;
        if (images[i].revisedPrompt)
            caption += `\nRevised prompt: ${images[i].revisedPrompt}`;
        content.push({ type: "text", text: caption });
    }
    return { content };
}
export function errorResponse(err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
        content: [{ type: "text", text: `Error: ${msg}` }],
        isError: true,
    };
}
