import { i as normalizeLowercaseStringOrEmpty } from "../../string-coerce-BUSzWgUA.js";
import { i as PASSTHROUGH_GEMINI_REPLAY_HOOKS, l as matchesExactOrPrefix } from "../../provider-model-shared-DGE-gkIc.js";
import "../../text-runtime-BZ19VEh4.js";
import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as OPENCODE_ZEN_DEFAULT_MODEL } from "../../provider-onboard-CqoaSwsU.js";
import { t as createOpencodeCatalogApiKeyAuthMethod } from "../../opencode-BJ6VLa6Q.js";
import { n as applyOpencodeZenConfig } from "../../onboard-DAeMkQaV.js";
//#region extensions/opencode/index.ts
const PROVIDER_ID = "opencode";
const MINIMAX_MODERN_MODEL_MATCHERS = ["minimax-m2.7"];
function isModernOpencodeModel(modelId) {
	const lower = normalizeLowercaseStringOrEmpty(modelId);
	if (lower.endsWith("-free") || lower === "alpha-glm-4.7") return false;
	return !matchesExactOrPrefix(lower, MINIMAX_MODERN_MODEL_MATCHERS);
}
var opencode_default = definePluginEntry({
	id: PROVIDER_ID,
	name: "OpenCode Zen Provider",
	description: "Bundled OpenCode Zen provider plugin",
	register(api) {
		api.registerProvider({
			id: PROVIDER_ID,
			label: "OpenCode Zen",
			docsPath: "/providers/models",
			envVars: ["OPENCODE_API_KEY", "OPENCODE_ZEN_API_KEY"],
			auth: [createOpencodeCatalogApiKeyAuthMethod({
				providerId: PROVIDER_ID,
				label: "OpenCode Zen catalog",
				optionKey: "opencodeZenApiKey",
				flagName: "--opencode-zen-api-key",
				defaultModel: OPENCODE_ZEN_DEFAULT_MODEL,
				applyConfig: (cfg) => applyOpencodeZenConfig(cfg),
				noteMessage: [
					"OpenCode uses one API key across the Zen and Go catalogs.",
					"Zen provides access to Claude, GPT, Gemini, and more models.",
					"Get your API key at: https://opencode.ai/auth",
					"Choose the Zen catalog when you want the curated multi-model proxy."
				].join("\n"),
				choiceId: "opencode-zen",
				choiceLabel: "OpenCode Zen catalog"
			})],
			...PASSTHROUGH_GEMINI_REPLAY_HOOKS,
			isModernModelRef: ({ modelId }) => isModernOpencodeModel(modelId)
		});
	}
});
//#endregion
export { opencode_default as default };
