import "./subsystem-Dk33jKDp.js";
import "./provider-env-vars-DlIUdRdT.js";
import "./failover-error-UqfEyPkm.js";
import "./provider-registry-GMOGSD5r.js";
import "./runtime-shared-BY6UjFo-.js";
import "./provider-model-shared-DGE-gkIc.js";
import "./provider-model-defaults-DmBOJ_vj.js";
//#region src/plugin-sdk/image-generation-core.ts
let imageGenerationCoreAuthRuntimePromise;
async function loadImageGenerationCoreAuthRuntime() {
	imageGenerationCoreAuthRuntimePromise ??= import("./image-generation-core.auth.runtime-CLiOcXg1.js");
	return imageGenerationCoreAuthRuntimePromise;
}
async function resolveApiKeyForProvider(...args) {
	return (await loadImageGenerationCoreAuthRuntime()).resolveApiKeyForProvider(...args);
}
//#endregion
export { resolveApiKeyForProvider as t };
