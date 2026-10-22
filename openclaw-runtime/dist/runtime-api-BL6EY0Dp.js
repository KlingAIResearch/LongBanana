import "./core-BRrvsWXZ.js";
import "./secret-input-U_-hh94N.js";
import { t as createPluginRuntimeStore } from "./runtime-store-CMoSfmpu.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import "./channel-pairing-Cgn4Qxx9.js";
import "./status-helpers-X5NGYozQ.js";
import "./webhook-ingress-d3B1liDG.js";
import "./runtime-CsAFtiSZ.js";
import "./setup-C1V4nBvJ.js";
import "./config-runtime-D3fBpUtu.js";
import "./command-auth-CYjgHdZt.js";
import "./channel-feedback-B95OnBI7.js";
import "./channel-status-Dk3XN6xu.js";
//#region extensions/zalo/src/runtime.ts
const { setRuntime: setZaloRuntime, getRuntime: getZaloRuntime } = createPluginRuntimeStore({
	pluginId: "zalo",
	errorMessage: "Zalo runtime not initialized"
});
//#endregion
export { setZaloRuntime as n, getZaloRuntime as t };
