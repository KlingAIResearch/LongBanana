import { n as resolvePreferredOpenClawTmpDir } from "../tmp-openclaw-dir-BobVQuve.js";
import { h as MarkdownConfigSchema } from "../zod-schema.core-gdcGSc89.js";
import { r as buildChannelConfigSchema } from "../config-schema-B5e-FOo2.js";
import { n as normalizeAccountId, t as DEFAULT_ACCOUNT_ID } from "../account-id-BuseNZr0.js";
import { c as ToolPolicySchema } from "../zod-schema.agent-runtime-XcBhqA_b.js";
import { i as loadBundledPluginPublicSurfaceModuleSync } from "../facade-loader-CxAG8qn9.js";
import { d as resolveOutboundMediaUrls, h as sendMediaWithLeadingCaption, i as deliverTextOrMediaReply, l as isNumericTargetId, p as resolveSendableOutboundReplyParts, y as sendPayloadWithChunkedTextAndMedia } from "../reply-payload-DNewKWND.js";
import { n as deleteAccountFromConfigSection, r as setAccountEnabledInConfigSection } from "../config-helpers-DLZrC8Fr.js";
import { t as createAccountListHelpers } from "../account-helpers-B8-OixoH.js";
import { n as formatPairingApproveHint } from "../helpers-CS5OE-XO.js";
import { n as emptyPluginConfigSchema } from "../config-schema-ByMpA8_M.js";
import { l as patchScopedAccountConfig, n as applySetupAccountConfigPatch, s as migrateBaseNameToDefaultAccount, t as applyAccountNameToChannelSection } from "../setup-helpers-CXFAhexK.js";
import { i as resolveMentionGatingWithBypass, n as resolveInboundMentionDecision, r as resolveMentionGating } from "../mention-gating-Bkgx3XYF.js";
import { i as mergeAllowlist, o as summarizeMapping } from "../resolve-utils-Ctxlj-T-.js";
import { t as formatAllowFromLowercase } from "../allow-from-BsldHaeo.js";
import { a as warnMissingProviderGroupPolicyFallbackOnce, i as resolveOpenProviderRuntimeGroupPolicy, r as resolveDefaultGroupPolicy } from "../runtime-group-policy-BRDAcBG-.js";
import { n as isDangerousNameMatchingEnabled } from "../dangerous-name-matching-BslXQKL6.js";
import { a as resolveSenderScopedGroupPolicy, t as evaluateGroupRouteAccessForPolicy } from "../group-access-axbYCita.js";
import { X as setTopLevelChannelDmPolicyWithAllowFrom, t as addWildcardAllowFrom, v as mergeAllowFromEntries } from "../setup-wizard-helpers-C3fKdzMA.js";
import { t as createChannelReplyPipeline } from "../channel-reply-pipeline-Bh3Tpm_u.js";
import { n as createChannelPairingController } from "../channel-pairing-Cgn4Qxx9.js";
import { t as buildBaseAccountStatusSnapshot } from "../status-helpers-X5NGYozQ.js";
import { t as formatResolvedUnresolvedNote } from "../setup-C1V4nBvJ.js";
import { t as createOptionalChannelSetupSurface } from "../channel-setup-C-4z27M0.js";
import { t as loadOutboundMediaFromUrl } from "../outbound-media-BhrhlrIy.js";
import { t as chunkTextForOutbound } from "../text-chunking-DFXq7qu-.js";
import { a as resolveSenderCommandAuthorization } from "../command-auth-CYjgHdZt.js";
import { r as buildChannelSendResult } from "../channel-send-result-MXXyZN8q.js";
import { t as resolveChannelAccountConfigBasePath } from "../config-paths-DAs0Filr.js";
//#region src/plugin-sdk/zalouser.ts
function loadFacadeModule() {
	return loadBundledPluginPublicSurfaceModuleSync({
		dirName: "zalouser",
		artifactBasename: "contract-api.js"
	});
}
const collectZalouserSecurityAuditFindings = ((...args) => loadFacadeModule().collectZalouserSecurityAuditFindings(...args));
const zalouserSetup = createOptionalChannelSetupSurface({
	channel: "zalouser",
	label: "Zalo Personal",
	npmSpec: "@openclaw/zalouser",
	docsPath: "/channels/zalouser"
});
const zalouserSetupAdapter = zalouserSetup.setupAdapter;
const zalouserSetupWizard = zalouserSetup.setupWizard;
//#endregion
export { DEFAULT_ACCOUNT_ID, MarkdownConfigSchema, ToolPolicySchema, addWildcardAllowFrom, applyAccountNameToChannelSection, applySetupAccountConfigPatch, buildBaseAccountStatusSnapshot, buildChannelConfigSchema, buildChannelSendResult, chunkTextForOutbound, collectZalouserSecurityAuditFindings, createAccountListHelpers, createChannelPairingController, createChannelReplyPipeline, deleteAccountFromConfigSection, deliverTextOrMediaReply, emptyPluginConfigSchema, evaluateGroupRouteAccessForPolicy, formatAllowFromLowercase, formatPairingApproveHint, formatResolvedUnresolvedNote, isDangerousNameMatchingEnabled, isNumericTargetId, loadOutboundMediaFromUrl, mergeAllowFromEntries, mergeAllowlist, migrateBaseNameToDefaultAccount, normalizeAccountId, patchScopedAccountConfig, resolveChannelAccountConfigBasePath, resolveDefaultGroupPolicy, resolveInboundMentionDecision, resolveMentionGating, resolveMentionGatingWithBypass, resolveOpenProviderRuntimeGroupPolicy, resolveOutboundMediaUrls, resolvePreferredOpenClawTmpDir, resolveSendableOutboundReplyParts, resolveSenderCommandAuthorization, resolveSenderScopedGroupPolicy, sendMediaWithLeadingCaption, sendPayloadWithChunkedTextAndMedia, setAccountEnabledInConfigSection, setTopLevelChannelDmPolicyWithAllowFrom, summarizeMapping, warnMissingProviderGroupPolicyFallbackOnce, zalouserSetupAdapter, zalouserSetupWizard };
