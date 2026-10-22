import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { saveImages, errorResponse, resizeRefForSend } from "./_common.js";
import { generateWithGemini } from "./_gemini.js";
const server = new McpServer({ name: "image-gen-mcp-gemini", version: "3.0.0" });
server.tool("generate_image", "Generate an image via Gemini. References are absolute image paths. Full images are saved; visual previews are aspect-preserving, at most 1024 pixels.", {
  prompt: z.string().describe("Text description / edit instruction."),
  reference_images: z.array(z.string()).default([]).describe("Absolute paths to reference images."),
  output_dir: z.string().optional().describe("Save directory; defaults to /output."),
}, async (params) => {
  try {
    const images = await generateWithGemini({ prompt: params.prompt, refs: params.reference_images });
    const paths = await saveImages(images, params.output_dir || "/output");
    const content = [];
    for (let i = 0; i < images.length; i++) {
      const preview = await resizeRefForSend(Buffer.from(images[i].base64, "base64"), 1024);
      content.push({ type: "text", text: `Image ${i + 1} saved to: ${paths[i]} (original preserved; preview at most 1024 px)` });
      content.push({ type: "image", data: preview.bytes.toString("base64"), mimeType: preview.mime });
    }
    return { content };
  } catch (err) { return errorResponse(err); }
});
// Read images with the CLI's native view_image / Read tool, not another MCP.
await server.connect(new StdioServerTransport());
