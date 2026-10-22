// Preserve the existing generate_image MCP schema and response rendering.
// Only the HTTP transport changes; upstream credentials never enter the sandbox.
import { readFile } from "node:fs/promises";
import { resizeRefForSend } from "./_common.js";

export async function generateWithGemini(params) {
  const parts = [{ text: params.prompt }];
  for (const path of params.refs) {
    const { bytes, mime } = await resizeRefForSend(await readFile(path));
    parts.push({ inlineData: { mimeType: mime, data: bytes.toString("base64") } });
  }
  const response = await fetch(process.env.LONGBANANA_IMAGE_BRIDGE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + process.env.LONGBANANA_IMAGE_BRIDGE_TOKEN },
    body: JSON.stringify({ contents: [{ role: "user", parts }], generationConfig: { responseModalities: ["TEXT", "IMAGE"] } }),
    signal: AbortSignal.timeout(Number(process.env.MCP_TOOL_TIMEOUT || 1800000)),
  });
  if (!response.ok) throw new Error(`Image bridge HTTP ${response.status}`);
  const value = await response.json();
  for (const part of value.candidates?.[0]?.content?.parts || []) {
    const data = part.inlineData || part.inline_data;
    if (data?.data && (data.mimeType || data.mime_type || "").startsWith("image/")) {
      return [{ base64: data.data, mimeType: data.mimeType || data.mime_type }];
    }
  }
  throw new Error("Image bridge returned no image");
}
