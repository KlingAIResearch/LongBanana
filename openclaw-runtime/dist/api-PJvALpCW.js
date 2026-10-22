import { n as resolveAgentModelPrimaryValue } from "./model-input-rQYpOdVy.js";
import { n as applyAgentDefaultModelPrimary } from "./provider-onboard-CqoaSwsU.js";
import { t as OPENCODE_GO_DEFAULT_MODEL_REF } from "./onboard-BEig26qn.js";
//#region extensions/opencode-go/api.ts
function applyOpencodeGoModelDefault(cfg) {
	if (resolveAgentModelPrimaryValue(cfg.agents?.defaults?.model) === "opencode-go/kimi-k2.5") return {
		next: cfg,
		changed: false
	};
	return {
		next: applyAgentDefaultModelPrimary(cfg, OPENCODE_GO_DEFAULT_MODEL_REF),
		changed: true
	};
}
//#endregion
export { applyOpencodeGoModelDefault as t };
