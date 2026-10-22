import "./errors-D8p6rxH8.js";
import "./tmp-openclaw-dir-BobVQuve.js";
import "./env-DsEXAzhm.js";
import "./file-lock-DjDQcdsu.js";
import "./ssrf-CKxNXzEA.js";
import "./fetch-guard-BihRI978.js";
import "./fs-safe-aV1L_od6.js";
import "./exec-approvals-D7keheao.js";
import "./proxy-fetch-CAsiHSIe.js";
import "./undici-global-dispatcher-B89_EagU.js";
import { n as drainPendingDeliveries$1 } from "./delivery-queue-CX7kNtDu.js";
import "./system-events-THdlQ_p5.js";
import "./retry-DNBvHVd-.js";
import "./secret-file-Vbr71t4R.js";
import "./http-body-35ouPyQ5.js";
import "./exec-approval-reply-CsVWZzwg.js";
import "./approval-native-runtime-4eoWle0P.js";
import "./exec-approval-command-display-BZSsFstk.js";
import "./exec-approval-session-target-CXMlpAnM.js";
import "./heartbeat-visibility-DBGpilpF.js";
import "./transport-ready-CzfhOkU5.js";
import "./identity-Cv7e0oHu.js";
import "./retry-policy-COSUBAe5.js";
import "./ssrf-policy-D0O6hx0Q.js";
//#region src/plugin-sdk/infra-runtime.ts
function normalizeWhatsAppReconnectAccountId(accountId) {
	return (accountId ?? "").trim() || "default";
}
const WHATSAPP_NO_LISTENER_ERROR_RE = /No active WhatsApp Web listener/i;
let outboundDeliverRuntimePromise = null;
async function loadOutboundDeliverRuntime() {
	outboundDeliverRuntimePromise ??= import("./deliver-runtime-Df2v0-Zy.js");
	return await outboundDeliverRuntimePromise;
}
async function drainPendingDeliveries(opts) {
	const deliver = opts.deliver ?? (await loadOutboundDeliverRuntime()).deliverOutboundPayloads;
	await drainPendingDeliveries$1({
		...opts,
		deliver
	});
}
/**
* @deprecated Prefer plugin-owned reconnect policy wired through
* `drainPendingDeliveries(...)`. This compatibility shim preserves the
* historical public SDK symbol for existing plugin callers.
*/
async function drainReconnectQueue(opts) {
	const normalizedAccountId = normalizeWhatsAppReconnectAccountId(opts.accountId);
	await drainPendingDeliveries({
		drainKey: `whatsapp:${normalizedAccountId}`,
		logLabel: "WhatsApp reconnect drain",
		cfg: opts.cfg,
		log: opts.log,
		stateDir: opts.stateDir,
		deliver: opts.deliver,
		selectEntry: (entry) => ({
			match: entry.channel === "whatsapp" && normalizeWhatsAppReconnectAccountId(entry.accountId) === normalizedAccountId && typeof entry.lastError === "string" && WHATSAPP_NO_LISTENER_ERROR_RE.test(entry.lastError),
			bypassBackoff: true
		})
	});
}
//#endregion
export { drainReconnectQueue as n, drainPendingDeliveries as t };
