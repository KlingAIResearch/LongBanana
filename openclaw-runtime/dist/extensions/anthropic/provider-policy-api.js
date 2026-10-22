import { n as normalizeAnthropicProviderConfig, t as applyAnthropicConfigDefaults } from "../../config-defaults-Bet1SCnu.js";
//#region extensions/anthropic/provider-policy-api.ts
function normalizeConfig(params) {
	return normalizeAnthropicProviderConfig(params.providerConfig);
}
function applyConfigDefaults(params) {
	return applyAnthropicConfigDefaults(params);
}
//#endregion
export { applyConfigDefaults, normalizeConfig };
