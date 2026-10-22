import { r as redactSensitiveText } from "../redact-D4nea1HF.js";
import { t as formatDocsLink } from "../links-CdeABZi6.js";
import { a as hasConfiguredSecretInput, c as normalizeResolvedSecretInputString, l as normalizeSecretInputString } from "../types.secrets-DbVQrBMp.js";
import { s as isPrivateOrLoopbackHost } from "../net-CFf3KvYx.js";
import { s as normalizeStringEntries } from "../string-normalization-D69g5YYB.js";
import { h as MarkdownConfigSchema } from "../zod-schema.core-gdcGSc89.js";
import { r as buildChannelConfigSchema } from "../config-schema-B5e-FOo2.js";
import { u as resolveAgentIdFromSessionKey } from "../session-key-ZJPu_0qD.js";
import { n as normalizeAccountId, r as normalizeOptionalAccountId, t as DEFAULT_ACCOUNT_ID } from "../account-id-BuseNZr0.js";
import { s as getChatChannelMeta } from "../registry-CZ7mm4Ua.js";
import { c as ToolPolicySchema } from "../zod-schema.agent-runtime-XcBhqA_b.js";
import { i as resolveChannelEntryMatch, n as buildChannelKeyCandidates } from "../channel-config-TxpVg6Gf.js";
import { i as resolveAllowlistMatchByCandidates, n as formatAllowlistMatchMeta, o as resolveCompiledAllowlistMatch, r as resolveAllowlistCandidates, t as compileAllowlist } from "../allowlist-match-Bnpk97LV.js";
import { i as loadBundledPluginPublicSurfaceModuleSync, t as createLazyFacadeArrayValue } from "../facade-loader-CxAG8qn9.js";
import { t as resolveAckReaction } from "../identity-BN5OQFTZ.js";
import { n as fetchWithSsrFGuard } from "../fetch-guard-BihRI978.js";
import { c as jsonResult, d as readNumberParam, f as readReactionParams, h as readStringParam, i as createActionGate, p as readStringArrayParam } from "../common-B-eA4nK1.js";
import { r as getAgentScopedMediaLocalRoots } from "../local-roots-wAUbv0YN.js";
import { n as normalizePollInput } from "../polls-B78aNXvC.js";
import { t as resolveOutboundSendDep } from "../send-deps-ChgxnZ0n.js";
import { n as deleteAccountFromConfigSection, r as setAccountEnabledInConfigSection } from "../config-helpers-DLZrC8Fr.js";
import { n as writeJsonFileAtomically, t as readJsonFileWithFallback } from "../json-store-DMXCWMUe.js";
import { a as registerSessionBindingAdapter, o as unregisterSessionBindingAdapter, r as getSessionBindingService } from "../session-binding-service-DNPt8fBU.js";
import { t as createAccountListHelpers } from "../account-helpers-B8-OixoH.js";
import { n as formatPairingApproveHint } from "../helpers-CS5OE-XO.js";
import { n as emptyPluginConfigSchema } from "../config-schema-ByMpA8_M.js";
import { c as moveSingleAccountChannelSectionToDefaultAccount, t as applyAccountNameToChannelSection } from "../setup-helpers-CXFAhexK.js";
import { n as formatZonedTimestamp } from "../format-datetime-B4qg241f.js";
import { r as buildSecretInputSchema } from "../secret-input-U_-hh94N.js";
import { n as resolveControlCommandGate } from "../command-gating-CTt-rVWM.js";
import { a as patchAllowlistUsersInConfigEntries, i as mergeAllowlist, n as buildAllowlistResolutionSummary, o as summarizeMapping, r as canonicalizeAllowlistWithResolvedIds, t as addAllowlistUserEntriesFromConfigEntry } from "../resolve-utils-Ctxlj-T-.js";
import { a as warnMissingProviderGroupPolicyFallbackOnce, n as resolveAllowlistProviderRuntimeGroupPolicy, r as resolveDefaultGroupPolicy, t as GROUP_POLICY_BLOCKED_LABEL } from "../runtime-group-policy-BRDAcBG-.js";
import { a as resolveSenderScopedGroupPolicy, t as evaluateGroupRouteAccessForPolicy } from "../group-access-axbYCita.js";
import { n as logInboundDrop, r as logTypingFailure } from "../logging-Bz2L3CuY.js";
import { O as promptAccountId, P as promptSingleChannelSecretInput, Z as setTopLevelChannelGroupPolicy, n as buildSingleChannelSecretPromptState, t as addWildcardAllowFrom, v as mergeAllowFromEntries } from "../setup-wizard-helpers-C3fKdzMA.js";
import { t as PAIRING_APPROVED_MESSAGE } from "../pairing-message-0jf93unW.js";
import { n as createReplyPrefixOptions } from "../reply-prefix-CoQj0iXB.js";
import { t as createTypingCallbacks } from "../typing-CsJZFYfG.js";
import { t as createChannelReplyPipeline } from "../channel-reply-pipeline-Bh3Tpm_u.js";
import { n as createChannelPairingController } from "../channel-pairing-Cgn4Qxx9.js";
import { c as collectStatusIssuesFromLastError, i as buildProbeChannelStatusSummary, r as buildComputedAccountStatusSnapshot } from "../status-helpers-X5NGYozQ.js";
import { t as runPluginCommandWithTimeout } from "../run-command-BD8LU5RS.js";
import { n as resolveRuntimeEnv, t as createLoggerBackedRuntime } from "../runtime-logger-EPw40QxJ.js";
import "../runtime-CsAFtiSZ.js";
import { t as promptChannelAccessConfig } from "../setup-group-access-CIAXJ6ax.js";
import { t as formatResolvedUnresolvedNote } from "../setup-C1V4nBvJ.js";
import { t as createOptionalChannelSetupSurface } from "../channel-setup-C-4z27M0.js";
import { t as loadOutboundMediaFromUrl } from "../outbound-media-BhrhlrIy.js";
import { n as resolveThreadBindingFarewellText } from "../thread-bindings-messages-06bmL55A.js";
import { l as resolveThreadBindingMaxAgeMsForChannel, o as resolveThreadBindingIdleTimeoutMsForChannel } from "../thread-bindings-policy-CPuzBghV.js";
import { t as chunkTextForOutbound } from "../text-chunking-DFXq7qu-.js";
import "../channel-plugin-common-Dd_0J3t-.js";
import { n as toLocationContext, t as formatLocationText } from "../location-D3ieExin.js";
import { n as setMatrixThreadBindingMaxAgeBySessionKey, t as setMatrixThreadBindingIdleTimeoutBySessionKey } from "../matrix-thread-bindings-DNT8Hh16.js";
import { a as resolveMatrixAccountStorageRoot, c as resolveMatrixCredentialsPath, i as resolveConfiguredMatrixAccountIds, l as resolveMatrixDefaultOrOnlyAccountId, n as getMatrixScopedEnvVarNames, o as resolveMatrixChannelConfig, r as requiresExplicitMatrixDefaultAccount, s as resolveMatrixCredentialsDir, t as findMatrixAccountEntry, u as resolveMatrixLegacyFlatStoragePaths } from "../matrix-helper-B-uCJ8La.js";
import { n as setMatrixRuntime, t as resolveMatrixAccountStringValues } from "../matrix-runtime-surface-CVo96dqy.js";
import { r as resetMatrixThreadBindingsForTests, t as createMatrixThreadBindingManager } from "../matrix-surface-Djf5BCl8.js";
//#region src/plugin-sdk/matrix.ts
function loadMatrixFacadeModule() {
	return loadBundledPluginPublicSurfaceModuleSync({
		dirName: "matrix",
		artifactBasename: "contract-api.js"
	});
}
const singleAccountKeysToMove = createLazyFacadeArrayValue(() => loadMatrixFacadeModule().singleAccountKeysToMove);
const namedAccountPromotionKeys = createLazyFacadeArrayValue(() => loadMatrixFacadeModule().namedAccountPromotionKeys);
const resolveSingleAccountPromotionTarget = ((...args) => loadMatrixFacadeModule().resolveSingleAccountPromotionTarget(...args));
const matrixSetup = createOptionalChannelSetupSurface({
	channel: "matrix",
	label: "Matrix",
	npmSpec: "@openclaw/matrix",
	docsPath: "/channels/matrix"
});
const matrixSetupWizard = matrixSetup.setupWizard;
const matrixSetupAdapter = matrixSetup.setupAdapter;
//#endregion
export { DEFAULT_ACCOUNT_ID, GROUP_POLICY_BLOCKED_LABEL, MarkdownConfigSchema, PAIRING_APPROVED_MESSAGE, ToolPolicySchema, addAllowlistUserEntriesFromConfigEntry, addWildcardAllowFrom, applyAccountNameToChannelSection, buildAllowlistResolutionSummary, buildChannelConfigSchema, buildChannelKeyCandidates, buildComputedAccountStatusSnapshot, buildProbeChannelStatusSummary, buildSecretInputSchema, buildSingleChannelSecretPromptState, canonicalizeAllowlistWithResolvedIds, chunkTextForOutbound, collectStatusIssuesFromLastError, compileAllowlist, createAccountListHelpers, createActionGate, createChannelPairingController, createChannelReplyPipeline, createLoggerBackedRuntime, createMatrixThreadBindingManager, createReplyPrefixOptions, createTypingCallbacks, deleteAccountFromConfigSection, emptyPluginConfigSchema, evaluateGroupRouteAccessForPolicy, fetchWithSsrFGuard, findMatrixAccountEntry, formatAllowlistMatchMeta, formatDocsLink, formatLocationText, formatPairingApproveHint, formatResolvedUnresolvedNote, formatZonedTimestamp, getAgentScopedMediaLocalRoots, getChatChannelMeta, getMatrixScopedEnvVarNames, getSessionBindingService, hasConfiguredSecretInput, isPrivateOrLoopbackHost, jsonResult, loadOutboundMediaFromUrl, logInboundDrop, logTypingFailure, matrixSetupAdapter, matrixSetupWizard, mergeAllowFromEntries, mergeAllowlist, moveSingleAccountChannelSectionToDefaultAccount, namedAccountPromotionKeys, normalizeAccountId, normalizeOptionalAccountId, normalizePollInput, normalizeResolvedSecretInputString, normalizeSecretInputString, normalizeStringEntries, patchAllowlistUsersInConfigEntries, promptAccountId, promptChannelAccessConfig, promptSingleChannelSecretInput, readJsonFileWithFallback, readNumberParam, readReactionParams, readStringArrayParam, readStringParam, redactSensitiveText, registerSessionBindingAdapter, requiresExplicitMatrixDefaultAccount, resetMatrixThreadBindingsForTests, resolveAckReaction, resolveAgentIdFromSessionKey, resolveAllowlistCandidates, resolveAllowlistMatchByCandidates, resolveAllowlistProviderRuntimeGroupPolicy, resolveChannelEntryMatch, resolveCompiledAllowlistMatch, resolveConfiguredMatrixAccountIds, resolveControlCommandGate, resolveDefaultGroupPolicy, resolveMatrixAccountStorageRoot, resolveMatrixAccountStringValues, resolveMatrixChannelConfig, resolveMatrixCredentialsDir, resolveMatrixCredentialsPath, resolveMatrixDefaultOrOnlyAccountId, resolveMatrixLegacyFlatStoragePaths, resolveOutboundSendDep, resolveRuntimeEnv, resolveSenderScopedGroupPolicy, resolveSingleAccountPromotionTarget, resolveThreadBindingFarewellText, resolveThreadBindingIdleTimeoutMsForChannel, resolveThreadBindingMaxAgeMsForChannel, runPluginCommandWithTimeout, setAccountEnabledInConfigSection, setMatrixRuntime, setMatrixThreadBindingIdleTimeoutBySessionKey, setMatrixThreadBindingMaxAgeBySessionKey, setTopLevelChannelGroupPolicy, singleAccountKeysToMove, summarizeMapping, toLocationContext, unregisterSessionBindingAdapter, warnMissingProviderGroupPolicyFallbackOnce, writeJsonFileAtomically };
