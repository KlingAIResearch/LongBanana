import { t as formatMatrixErrorMessage } from "./errors-Ba5M_uuU.js";
import { normalizeOptionalString } from "openclaw/plugin-sdk/string-coerce-runtime";
//#region extensions/matrix/src/plugin-entry.runtime.ts
function sendError(respond, err) {
	respond(false, { error: formatMatrixErrorMessage(err) });
}
async function ensureMatrixCryptoRuntime(...args) {
	const { ensureMatrixCryptoRuntime: ensureRuntime } = await import("./deps-DwZ_8T7G.js").then((n) => n.t);
	await ensureRuntime(...args);
}
async function handleVerifyRecoveryKey({ params, respond }) {
	try {
		const { verifyMatrixRecoveryKey } = await import("./verification-Bj3H4Bp0.js").then((n) => n.v);
		const key = normalizeOptionalString(params?.key);
		if (!key) {
			respond(false, { error: "key required" });
			return;
		}
		const result = await verifyMatrixRecoveryKey(key, { accountId: normalizeOptionalString(params?.accountId) });
		respond(result.success, result);
	} catch (err) {
		sendError(respond, err);
	}
}
async function handleVerificationBootstrap({ params, respond }) {
	try {
		const { bootstrapMatrixVerification } = await import("./verification-Bj3H4Bp0.js").then((n) => n.v);
		const result = await bootstrapMatrixVerification({
			accountId: normalizeOptionalString(params?.accountId),
			recoveryKey: typeof params?.recoveryKey === "string" ? params.recoveryKey : void 0,
			forceResetCrossSigning: params?.forceResetCrossSigning === true
		});
		respond(result.success, result);
	} catch (err) {
		sendError(respond, err);
	}
}
async function handleVerificationStatus({ params, respond }) {
	try {
		const { getMatrixVerificationStatus } = await import("./verification-Bj3H4Bp0.js").then((n) => n.v);
		respond(true, await getMatrixVerificationStatus({
			accountId: normalizeOptionalString(params?.accountId),
			includeRecoveryKey: params?.includeRecoveryKey === true
		}));
	} catch (err) {
		sendError(respond, err);
	}
}
//#endregion
export { ensureMatrixCryptoRuntime, handleVerificationBootstrap, handleVerificationStatus, handleVerifyRecoveryKey };
