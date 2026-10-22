# Gemini Image Generation — OpenClaw MCP Reference

The bundled `image-gen-mcp` server uses the official Gemini API by default.
Set `GEMINI_API_KEY` and use the provided image backend configuration.
Vertex AI is an explicit alternative; see [runtime setup](../running.md).
API credentials and provider selection are server-side, never tool arguments.

## Tool call

```text
generate_image(
  prompt=<string>,
  reference_images=[<absolute image path>, ...],
  output_dir=<optional directory>
)
```

One call returns one image. Call again to iterate. The server cannot switch
to Azure or Seedream through tool arguments.

## Reference images

The server reads local files, resizes them to a maximum long side of 1024 pixels
by default (`MAX_REF_LONG_SIDE` overrides this), and sends inline image parts in
the supplied order. It preserves aspect ratio. Model-specific reference limits
depend on the selected model; the tool schema does not impose a fixed count.

## Output and errors

The first returned image is saved under `output_dir` (by default,
`~/.image-gen-mcp/generated`). The MCP response includes the saved path and a
visual preview. `view_reference_image` is available to inspect images.

A missing API key, HTTP error, or response without image data is returned as a
tool error. Configured accounts are tried in rotation. The server sends the
prompt, references, and image/text response modalities; unsupported extra tool
arguments do not configure model-specific generation settings.

See [Google's image-generation documentation](https://ai.google.dev/gemini-api/docs/image-generation)
for the capabilities of the model available to your account.
