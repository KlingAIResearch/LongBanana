import "./session-binding-service-DNPt8fBU.js";
import "./binding-registry-BQz-Au4i.js";
import "./conversation-binding-Dp57M7AB.js";
import "./session-BKZQ1HZx.js";
import "./pairing-store-DrzXbvY3.js";
import "./dm-policy-shared-CVrajwZr.js";
import "./binding-targets-BzQVK1jH.js";
import "./binding-routing-BE8_nxta.js";
import "./thread-bindings-policy-CPuzBghV.js";
import "./pairing-labels-BgZgD3iH.js";
//#region src/channels/session-meta.ts
let inboundSessionRuntimePromise = null;
function loadInboundSessionRuntime() {
	inboundSessionRuntimePromise ??= import("./inbound.runtime-iGgY1VM3.js");
	return inboundSessionRuntimePromise;
}
async function recordInboundSessionMetaSafe(params) {
	const runtime = await loadInboundSessionRuntime();
	const storePath = runtime.resolveStorePath(params.cfg.session?.store, { agentId: params.agentId });
	try {
		await runtime.recordSessionMetaFromInbound({
			storePath,
			sessionKey: params.sessionKey,
			ctx: params.ctx
		});
	} catch (err) {
		params.onError?.(err);
	}
}
//#endregion
export { recordInboundSessionMetaSafe as t };
