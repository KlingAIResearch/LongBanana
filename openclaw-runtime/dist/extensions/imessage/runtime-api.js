import { r as buildChannelConfigSchema } from "../../config-schema-B5e-FOo2.js";
import { t as DEFAULT_ACCOUNT_ID } from "../../account-id-BuseNZr0.js";
import { r as IMessageConfigSchema } from "../../zod-schema.providers-core-Bzyf_1rd.js";
import { m as formatTrimmedAllowFromEntries } from "../../channel-config-helpers-CP9RBkAj.js";
import { o as getChatChannelMeta } from "../../core-BRrvsWXZ.js";
import { t as createPluginRuntimeStore } from "../../runtime-store-CMoSfmpu.js";
import { t as resolveChannelMediaMaxBytes } from "../../media-limits-DUiU2W8d.js";
import { t as PAIRING_APPROVED_MESSAGE } from "../../pairing-message-0jf93unW.js";
import { c as collectStatusIssuesFromLastError, r as buildComputedAccountStatusSnapshot } from "../../status-helpers-X5NGYozQ.js";
import "../../media-runtime-Ka5nWe-e.js";
import { t as chunkTextForOutbound } from "../../text-chunking-DFXq7qu-.js";
import "../../channel-status-Dk3XN6xu.js";
import { _ as resolveIMessageConfigAllowFrom, g as normalizeIMessageMessagingTarget, h as looksLikeIMessageTargetId, t as probeIMessage, v as resolveIMessageConfigDefaultTo } from "../../probe-DRnMFj8L.js";
import { n as resolveIMessageGroupToolPolicy, t as resolveIMessageGroupRequireMention } from "../../group-policy-BIZQy8VZ.js";
import "../../config-api-Cubow1zJ.js";
import { n as sendMessageIMessage, t as monitorIMessageProvider } from "../../monitor-DpifAzX-.js";
//#region extensions/imessage/src/runtime.ts
const { setRuntime: setIMessageRuntime, getRuntime: getIMessageRuntime } = createPluginRuntimeStore({
	pluginId: "imessage",
	errorMessage: "iMessage runtime not initialized"
});
//#endregion
export { DEFAULT_ACCOUNT_ID, IMessageConfigSchema, PAIRING_APPROVED_MESSAGE, buildChannelConfigSchema, buildComputedAccountStatusSnapshot, chunkTextForOutbound, collectStatusIssuesFromLastError, formatTrimmedAllowFromEntries, getChatChannelMeta, looksLikeIMessageTargetId, monitorIMessageProvider, normalizeIMessageMessagingTarget, probeIMessage, resolveChannelMediaMaxBytes, resolveIMessageConfigAllowFrom, resolveIMessageConfigDefaultTo, resolveIMessageGroupRequireMention, resolveIMessageGroupToolPolicy, sendMessageIMessage, setIMessageRuntime };
