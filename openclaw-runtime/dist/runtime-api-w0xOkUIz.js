import { t as createPluginRuntimeStore } from "./runtime-store-CMoSfmpu.js";
import "./channel-policy-B_ra2Ydm.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import "./channel-pairing-Cgn4Qxx9.js";
import "./webhook-request-guards-CMqInOkA.js";
import "./webhook-targets-CGL7Z-hL.js";
import "./config-runtime-D3fBpUtu.js";
import "./outbound-media-BhrhlrIy.js";
import "./ssrf-runtime-7jqXypIM.js";
import "./media-runtime-Ka5nWe-e.js";
import "./channel-config-primitives-DvzEQCyl.js";
import "./channel-actions-DkD19cHj.js";
import "./channel-feedback-B95OnBI7.js";
import "./channel-inbound-BLJhwJOR.js";
import "./channel-lifecycle-C8Ly-mbq.js";
import "./googlechat-runtime-shared-B7QMKmYI.js";
import "./channel-status-Dk3XN6xu.js";
//#region extensions/googlechat/src/runtime.ts
const { setRuntime: setGoogleChatRuntime, getRuntime: getGoogleChatRuntime } = createPluginRuntimeStore({
	pluginId: "googlechat",
	errorMessage: "Google Chat runtime not initialized"
});
//#endregion
export { setGoogleChatRuntime as n, getGoogleChatRuntime as t };
