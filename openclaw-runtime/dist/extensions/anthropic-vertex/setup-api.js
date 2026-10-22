import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { i as resolveAnthropicVertexConfigApiKey } from "../../region-DXMT-6VF.js";
//#region extensions/anthropic-vertex/setup-api.ts
var setup_api_default = definePluginEntry({
	id: "anthropic-vertex",
	name: "Anthropic Vertex Setup",
	description: "Lightweight Anthropic Vertex setup hooks",
	register(api) {
		api.registerProvider({
			id: "anthropic-vertex",
			label: "Anthropic Vertex",
			auth: [],
			resolveConfigApiKey: ({ env }) => resolveAnthropicVertexConfigApiKey(env)
		});
	}
});
//#endregion
export { setup_api_default as default };
