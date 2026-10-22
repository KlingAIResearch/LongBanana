import { d as readStringValue } from "./string-coerce-BUSzWgUA.js";
import { r as normalizeProviderId } from "./provider-id-CgvrAT-R.js";
import { r as resolveProviderEndpoint } from "./provider-attribution-CQYqYaLk.js";
import "./provider-tools-BEjp4Q9-.js";
import { o as getModelProviderHint } from "./provider-model-shared-DGE-gkIc.js";
import "./text-runtime-BZ19VEh4.js";
import "./model-definitions-CGKxBfun.js";
import "./provider-catalog-BN-rEcHt.js";
import "./onboard-iRhwEAcy2.js";
import "./provider-models-CCCsmoor.js";
//#region extensions/xai/api.ts
function isXaiNativeEndpoint(baseUrl) {
	return typeof baseUrl === "string" && resolveProviderEndpoint(baseUrl).endpointClass === "xai-native";
}
function isXaiModelHint(modelId) {
	return getModelProviderHint(modelId) === "x-ai";
}
function shouldUseXaiResponsesTransport(params) {
	if (params.api !== "openai-completions") return false;
	if (isXaiNativeEndpoint(params.baseUrl)) return true;
	return normalizeProviderId(params.provider) === "xai" && !params.baseUrl;
}
function shouldContributeXaiCompat(params) {
	if (params.model.api !== "openai-completions") return false;
	return isXaiNativeEndpoint(params.model.baseUrl) || isXaiModelHint(params.modelId);
}
function resolveXaiTransport(params) {
	if (!shouldUseXaiResponsesTransport(params)) return;
	return {
		api: "openai-responses",
		baseUrl: readStringValue(params.baseUrl)
	};
}
//#endregion
export { resolveXaiTransport as n, shouldContributeXaiCompat as r, isXaiModelHint as t };
