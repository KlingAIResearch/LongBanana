#!/usr/bin/env node
/**
 * MCP server dedicated to Gemini image generation (official API or Vertex AI).
 * Only imports _gemini + _common — physically cannot route to Azure or Seedream.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { DEFAULT_OUTPUT_DIR, errorResponse, makeLogger, registerViewTool, renderGenerateResponse, saveImages, } from "./_common.js";
import { generateWithGemini } from "./_gemini.js";
const log = makeLogger("image-gen-mcp-gemini");
const server = new McpServer({ name: "image-gen-mcp-gemini", version: "3.0.0" });
server.tool("generate_image", "Generate an image via Gemini. Provide reference_images as absolute paths; they are inlined as parts in the multimodal request.", {
    prompt: z.string().describe("Text description / edit instruction."),
    reference_images: z.array(z.string()).default([]).describe("Absolute paths to reference images. Inlined as multimodal parts."),
    output_dir: z.string().optional().describe("Directory to save images. Default: ~/.image-gen-mcp/generated"),
}, async (params) => {
    try {
        const outDir = params.output_dir || DEFAULT_OUTPUT_DIR;
        const images = await generateWithGemini({
            prompt: params.prompt,
            refs: params.reference_images,
        });
        const saved = await saveImages(images, outDir);
        return renderGenerateResponse(images, saved, "gemini");
    }
    catch (err) {
        return errorResponse(err);
    }
});
registerViewTool(server);
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    log("server running on stdio (gemini-only, v3)");
}
main().catch((err) => {
    console.error("Fatal:", err);
    process.exit(1);
});
