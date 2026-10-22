import "./provider-model-shared-DGE-gkIc.js";
import "./core-BRrvsWXZ.js";
import "./routing-DNlUaOwT.js";
import { t as createPluginRuntimeStore } from "./runtime-store-CMoSfmpu.js";
import "./channel-policy-B_ra2Ydm.js";
import "./reply-history-CxAAiNeS.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import "./channel-pairing-Cgn4Qxx9.js";
import "./webhook-targets-CGL7Z-hL.js";
import "./webhook-ingress-d3B1liDG.js";
import "./setup-C1V4nBvJ.js";
import "./config-runtime-D3fBpUtu.js";
import "./agent-media-payload-D5PJ1y7U.js";
import "./outbound-media-BhrhlrIy.js";
import "./media-runtime-Ka5nWe-e.js";
import "./browser-node-runtime-DHoRoWns.js";
import "./command-auth-CYjgHdZt.js";
import "./channel-feedback-B95OnBI7.js";
import "./channel-inbound-BLJhwJOR.js";
import "./channel-lifecycle-C8Ly-mbq.js";
import "./channel-status-Dk3XN6xu.js";
//#region extensions/mattermost/src/runtime.ts
const { setRuntime: setMattermostRuntime, getRuntime: getMattermostRuntime } = createPluginRuntimeStore({
	pluginId: "mattermost",
	errorMessage: "Mattermost runtime not initialized"
});
//#endregion
export { setMattermostRuntime as n, getMattermostRuntime as t };
