import { t as __exportAll } from "./rolldown-runtime-DUslC3ob.js";
import { t as getMatrixScopedEnvVarNames } from "./env-vars-CpXNsTJq.js";
import { t as isBunRuntime } from "./runtime-rzhzT7mI.js";
import { a as resolveMatrixConfigForAccount, c as resolveValidatedMatrixHomeserverUrl, i as resolveMatrixAuthContext, l as validateMatrixHomeserverUrl, n as hasReadyMatrixEnvAuth, o as resolveMatrixEnvAuthReadiness, r as resolveMatrixAuth, s as resolveScopedMatrixEnvConfig, t as backfillMatrixAuthDeviceIdAfterStartup } from "./config-Cdv96QZL.js";
import { t as createMatrixClient } from "./create-client-D1VmSA57.js";
import { i as resolveSharedMatrixClient, n as releaseSharedClientInstance, o as stopSharedClientForAccount, r as removeSharedClientInstance, s as stopSharedClientInstance, t as acquireSharedMatrixClient } from "./shared-aVhY5YY0.js";
//#region extensions/matrix/src/matrix/client.ts
var client_exports = /* @__PURE__ */ __exportAll({
	acquireSharedMatrixClient: () => acquireSharedMatrixClient,
	backfillMatrixAuthDeviceIdAfterStartup: () => backfillMatrixAuthDeviceIdAfterStartup,
	createMatrixClient: () => createMatrixClient,
	getMatrixScopedEnvVarNames: () => getMatrixScopedEnvVarNames,
	hasReadyMatrixEnvAuth: () => hasReadyMatrixEnvAuth,
	isBunRuntime: () => isBunRuntime,
	releaseSharedClientInstance: () => releaseSharedClientInstance,
	removeSharedClientInstance: () => removeSharedClientInstance,
	resolveMatrixAuth: () => resolveMatrixAuth,
	resolveMatrixAuthContext: () => resolveMatrixAuthContext,
	resolveMatrixConfigForAccount: () => resolveMatrixConfigForAccount,
	resolveMatrixEnvAuthReadiness: () => resolveMatrixEnvAuthReadiness,
	resolveScopedMatrixEnvConfig: () => resolveScopedMatrixEnvConfig,
	resolveSharedMatrixClient: () => resolveSharedMatrixClient,
	resolveValidatedMatrixHomeserverUrl: () => resolveValidatedMatrixHomeserverUrl,
	stopSharedClientForAccount: () => stopSharedClientForAccount,
	stopSharedClientInstance: () => stopSharedClientInstance,
	validateMatrixHomeserverUrl: () => validateMatrixHomeserverUrl
});
//#endregion
export { client_exports as t };
