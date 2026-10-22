import { n as readSessionUpdatedAt } from "./store-BQPg58te.js";
import "./sessions-ULJtkV29.js";
import { u as resolveStorePath } from "./paths-WKsTZdeA.js";
import { a as resolveEnvelopeFormatOptions } from "./envelope-C-afrtUd.js";
//#region src/channels/session-envelope.ts
function resolveInboundSessionEnvelopeContext(params) {
	const storePath = resolveStorePath(params.cfg.session?.store, { agentId: params.agentId });
	return {
		storePath,
		envelopeOptions: resolveEnvelopeFormatOptions(params.cfg),
		previousTimestamp: readSessionUpdatedAt({
			storePath,
			sessionKey: params.sessionKey
		})
	};
}
//#endregion
export { resolveInboundSessionEnvelopeContext as t };
