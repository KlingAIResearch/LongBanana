import { n as registerMatrixCliMetadata } from "./cli-metadata-bRuRntml.js";
import { defineBundledChannelEntry } from "openclaw/plugin-sdk/channel-entry-contract";
import { formatErrorMessage } from "openclaw/plugin-sdk/error-runtime";
//#region extensions/matrix/index.ts
let matrixSubagentHooksPromise = null;
function loadMatrixSubagentHooksModule() {
	matrixSubagentHooksPromise ??= import("./subagent-hooks-XLl_jtyY.js");
	return matrixSubagentHooksPromise;
}
function registerMatrixFullRuntime(api) {
	import("./plugin-entry.handlers.runtime.js").then(({ ensureMatrixCryptoRuntime }) => ensureMatrixCryptoRuntime({ log: api.logger.info }).catch((err) => {
		const message = formatErrorMessage(err);
		api.logger.warn?.(`matrix: crypto runtime bootstrap failed: ${message}`);
	})).catch((err) => {
		const message = formatErrorMessage(err);
		api.logger.warn?.(`matrix: failed loading crypto bootstrap runtime: ${message}`);
	});
	api.registerGatewayMethod("matrix.verify.recoveryKey", async (ctx) => {
		const { handleVerifyRecoveryKey } = await import("./plugin-entry.handlers.runtime.js");
		await handleVerifyRecoveryKey(ctx);
	});
	api.registerGatewayMethod("matrix.verify.bootstrap", async (ctx) => {
		const { handleVerificationBootstrap } = await import("./plugin-entry.handlers.runtime.js");
		await handleVerificationBootstrap(ctx);
	});
	api.registerGatewayMethod("matrix.verify.status", async (ctx) => {
		const { handleVerificationStatus } = await import("./plugin-entry.handlers.runtime.js");
		await handleVerificationStatus(ctx);
	});
	api.on("subagent_spawning", async (event) => {
		const { handleMatrixSubagentSpawning } = await loadMatrixSubagentHooksModule();
		return await handleMatrixSubagentSpawning(api, event);
	});
	api.on("subagent_ended", async (event) => {
		const { handleMatrixSubagentEnded } = await loadMatrixSubagentHooksModule();
		await handleMatrixSubagentEnded(event);
	});
	api.on("subagent_delivery_target", async (event) => {
		const { handleMatrixSubagentDeliveryTarget } = await loadMatrixSubagentHooksModule();
		return handleMatrixSubagentDeliveryTarget(event);
	});
}
var matrix_default = defineBundledChannelEntry({
	id: "matrix",
	name: "Matrix",
	description: "Matrix channel plugin (matrix-js-sdk)",
	importMetaUrl: import.meta.url,
	plugin: {
		specifier: "./channel-plugin-api.js",
		exportName: "matrixPlugin"
	},
	secrets: {
		specifier: "./secret-contract-api.js",
		exportName: "channelSecrets"
	},
	runtime: {
		specifier: "./runtime-api.js",
		exportName: "setMatrixRuntime"
	},
	registerCliMetadata: registerMatrixCliMetadata,
	registerFull: registerMatrixFullRuntime
});
//#endregion
export { matrix_default as default, registerMatrixFullRuntime };
