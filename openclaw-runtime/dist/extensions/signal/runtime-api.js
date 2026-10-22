import { u as normalizeE164 } from "../../utils-D5DtWkEu.js";
import { t as formatDocsLink } from "../../links-CdeABZi6.js";
import { t as formatCliCommand } from "../../command-format-w0VjgAOT.js";
import { r as buildChannelConfigSchema } from "../../config-schema-B5e-FOo2.js";
import { n as normalizeAccountId, t as DEFAULT_ACCOUNT_ID } from "../../account-id-BuseNZr0.js";
import { a as SignalConfigSchema } from "../../zod-schema.providers-core-Bzyf_1rd.js";
import { a as chunkText } from "../../chunk-Czf-8-kf.js";
import { n as deleteAccountFromConfigSection, r as setAccountEnabledInConfigSection } from "../../config-helpers-DLZrC8Fr.js";
import "../../text-runtime-BZ19VEh4.js";
import { n as formatPairingApproveHint } from "../../helpers-CS5OE-XO.js";
import { n as emptyPluginConfigSchema } from "../../config-schema-ByMpA8_M.js";
import { s as migrateBaseNameToDefaultAccount, t as applyAccountNameToChannelSection } from "../../setup-helpers-CXFAhexK.js";
import { o as getChatChannelMeta } from "../../core-BRrvsWXZ.js";
import { t as createPluginRuntimeStore } from "../../runtime-store-CMoSfmpu.js";
import { n as resolveAllowlistProviderRuntimeGroupPolicy, r as resolveDefaultGroupPolicy } from "../../runtime-group-policy-BRDAcBG-.js";
import { t as resolveChannelMediaMaxBytes } from "../../media-limits-DUiU2W8d.js";
import { t as PAIRING_APPROVED_MESSAGE } from "../../pairing-message-0jf93unW.js";
import { c as collectStatusIssuesFromLastError, d as createDefaultChannelRuntimeState, n as buildBaseChannelStatusSummary, t as buildBaseAccountStatusSnapshot } from "../../status-helpers-X5NGYozQ.js";
import { t as detectBinary } from "../../detect-binary-BoNPzlfL.js";
import "../../setup-tools-DOnhMcLe.js";
import "../../config-runtime-D3fBpUtu.js";
import "../../reply-runtime-CiahPHgH.js";
import "../../media-runtime-Ka5nWe-e.js";
import "../../channel-status-Dk3XN6xu.js";
import { i as resolveSignalAccount, n as listSignalAccountIds, r as resolveDefaultSignalAccountId, t as listEnabledSignalAccounts } from "../../accounts-BKHATEnE.js";
import { d as looksLikeSignalTargetId, f as normalizeSignalMessagingTarget } from "../../identity-D2vdtopu.js";
import { t as sendMessageSignal } from "../../send-CiP8tcGn.js";
import { n as sendReactionSignal, t as removeReactionSignal } from "../../reaction-runtime-api-DvL7Nt5v.js";
import { n as resolveSignalReactionLevel, t as signalMessageActions } from "../../message-actions-BaDxetKw.js";
import "../../config-api-D4EtvhI7.js";
import { n as installSignalCli } from "../../install-signal-cli-DBhnstW4.js";
import { t as monitorSignalProvider } from "../../monitor-TlBJefPl.js";
import { t as probeSignal } from "../../probe-mFoNZYSg.js";
//#region extensions/signal/src/runtime.ts
const { setRuntime: setSignalRuntime, clearRuntime: clearSignalRuntime, getRuntime: getSignalRuntime } = createPluginRuntimeStore({
	pluginId: "signal",
	errorMessage: "Signal runtime not initialized"
});
//#endregion
export { DEFAULT_ACCOUNT_ID, PAIRING_APPROVED_MESSAGE, SignalConfigSchema, applyAccountNameToChannelSection, buildBaseAccountStatusSnapshot, buildBaseChannelStatusSummary, buildChannelConfigSchema, chunkText, collectStatusIssuesFromLastError, createDefaultChannelRuntimeState, deleteAccountFromConfigSection, detectBinary, emptyPluginConfigSchema, formatCliCommand, formatDocsLink, formatPairingApproveHint, getChatChannelMeta, installSignalCli, listEnabledSignalAccounts, listSignalAccountIds, looksLikeSignalTargetId, migrateBaseNameToDefaultAccount, monitorSignalProvider, normalizeAccountId, normalizeE164, normalizeSignalMessagingTarget, probeSignal, removeReactionSignal, resolveAllowlistProviderRuntimeGroupPolicy, resolveChannelMediaMaxBytes, resolveDefaultGroupPolicy, resolveDefaultSignalAccountId, resolveSignalAccount, resolveSignalReactionLevel, sendMessageSignal, sendReactionSignal, setAccountEnabledInConfigSection, setSignalRuntime, signalMessageActions };
