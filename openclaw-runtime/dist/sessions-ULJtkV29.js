import { a as loadConfig } from "./io-zyJwuhrD.js";
import "./store-BQPg58te.js";
import { i as resolveMainSessionKey } from "./main-session-BBC2g05K.js";
import { u as resolveStorePath } from "./paths-WKsTZdeA.js";
import "./reset-0g5m7uIo.js";
import "./session-key-o9mQz71a.js";
import { t as deliveryContextFromSession } from "./delivery-context.shared-B2Qa-658.js";
import { t as loadSessionStore } from "./store-load-RjC_NzkA.js";
import "./transcript-DLndgEjc.js";
import { t as parseSessionThreadInfo } from "./thread-info-BgkBjXcm.js";
import "./targets-VYTKCc06.js";
//#region src/config/sessions/main-session.runtime.ts
function resolveMainSessionKeyFromConfig() {
	return resolveMainSessionKey(loadConfig());
}
//#endregion
//#region src/config/sessions/delivery-info.ts
function extractDeliveryInfo(sessionKey) {
	const hasRoutableDeliveryContext = (context) => Boolean(context?.channel && context?.to);
	const { baseSessionKey, threadId } = parseSessionThreadInfo(sessionKey);
	if (!sessionKey || !baseSessionKey) return {
		deliveryContext: void 0,
		threadId
	};
	let deliveryContext;
	try {
		const store = loadSessionStore(resolveStorePath(loadConfig().session?.store));
		let entry = store[sessionKey];
		let storedDeliveryContext = deliveryContextFromSession(entry);
		if (!hasRoutableDeliveryContext(storedDeliveryContext) && baseSessionKey !== sessionKey) {
			entry = store[baseSessionKey];
			storedDeliveryContext = deliveryContextFromSession(entry);
		}
		if (hasRoutableDeliveryContext(storedDeliveryContext)) deliveryContext = {
			channel: storedDeliveryContext.channel,
			to: storedDeliveryContext.to,
			accountId: storedDeliveryContext.accountId,
			threadId: storedDeliveryContext.threadId != null ? String(storedDeliveryContext.threadId) : void 0
		};
	} catch {}
	return {
		deliveryContext,
		threadId
	};
}
//#endregion
export { resolveMainSessionKeyFromConfig as n, extractDeliveryInfo as t };
