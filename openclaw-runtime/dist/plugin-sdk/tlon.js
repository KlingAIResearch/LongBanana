import { t as formatDocsLink } from "../links-CdeABZi6.js";
import { r as buildChannelConfigSchema } from "../config-schema-B5e-FOo2.js";
import { n as normalizeAccountId, t as DEFAULT_ACCOUNT_ID } from "../account-id-BuseNZr0.js";
import { t as createDedupeCache } from "../dedupe-B3fdYNcS.js";
import { c as isBlockedHostnameOrIp, t as SsrFBlockedError } from "../ssrf-CKxNXzEA.js";
import { n as fetchWithSsrFGuard } from "../fetch-guard-BihRI978.js";
import { n as emptyPluginConfigSchema } from "../config-schema-ByMpA8_M.js";
import { l as patchScopedAccountConfig, t as applyAccountNameToChannelSection } from "../setup-helpers-CXFAhexK.js";
import { t as createChannelReplyPipeline } from "../channel-reply-pipeline-Bh3Tpm_u.js";
import { r as buildComputedAccountStatusSnapshot } from "../status-helpers-X5NGYozQ.js";
import { t as createLoggerBackedRuntime } from "../runtime-logger-EPw40QxJ.js";
import "../runtime-CsAFtiSZ.js";
import { t as createOptionalChannelSetupSurface } from "../channel-setup-C-4z27M0.js";
//#region src/plugin-sdk/tlon.ts
const tlonSetup = createOptionalChannelSetupSurface({
	channel: "tlon",
	label: "Tlon",
	npmSpec: "@openclaw/tlon",
	docsPath: "/channels/tlon"
});
const tlonSetupAdapter = tlonSetup.setupAdapter;
const tlonSetupWizard = tlonSetup.setupWizard;
//#endregion
export { DEFAULT_ACCOUNT_ID, SsrFBlockedError, applyAccountNameToChannelSection, buildChannelConfigSchema, buildComputedAccountStatusSnapshot, createChannelReplyPipeline, createDedupeCache, createLoggerBackedRuntime, emptyPluginConfigSchema, fetchWithSsrFGuard, formatDocsLink, isBlockedHostnameOrIp, normalizeAccountId, patchScopedAccountConfig, tlonSetupAdapter, tlonSetupWizard };
