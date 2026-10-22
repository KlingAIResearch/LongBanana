import "./types.secrets-DbVQrBMp.js";
import "./ref-contract-D1tSJ7uu.js";
import "./provider-env-vars-DlIUdRdT.js";
import { n as ensureAuthProfileStore } from "./store-CLIgyp55.js";
import "./model-auth-markers-BosA_xbv.js";
import { t as resolveEnvApiKey } from "./model-auth-env-Bs8k9Q96.js";
import "./models-config.providers.secrets-CJFOB7Im.js";
import { n as listProfilesForProvider } from "./profiles-CugwjxkS.js";
import "./repair-DuY0n6Nr.js";
import "./provider-auth-input-B_rtbP_H.js";
import "./provider-auth-helpers-BvNYboQz.js";
import "./provider-api-key-auth-CU5upneV.js";
import { createHash, randomBytes } from "node:crypto";
//#region src/plugin-sdk/oauth-utils.ts
/** Encode a flat object as application/x-www-form-urlencoded form data. */
function toFormUrlEncoded(data) {
	return Object.entries(data).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join("&");
}
/** Generate a PKCE verifier/challenge pair suitable for OAuth authorization flows. */
function generatePkceVerifierChallenge() {
	const verifier = randomBytes(32).toString("base64url");
	return {
		verifier,
		challenge: createHash("sha256").update(verifier).digest("base64url")
	};
}
//#endregion
//#region src/plugin-sdk/provider-auth.ts
function isProviderApiKeyConfigured(params) {
	if (resolveEnvApiKey(params.provider)?.apiKey) return true;
	const agentDir = params.agentDir?.trim();
	if (!agentDir) return false;
	return listProfilesForProvider(ensureAuthProfileStore(agentDir, { allowKeychainPrompt: false }), params.provider).length > 0;
}
//#endregion
export { generatePkceVerifierChallenge as n, toFormUrlEncoded as r, isProviderApiKeyConfigured as t };
