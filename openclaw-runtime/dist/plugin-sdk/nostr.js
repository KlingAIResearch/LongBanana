import { h as MarkdownConfigSchema } from "../zod-schema.core-gdcGSc89.js";
import { r as buildChannelConfigSchema } from "../config-schema-B5e-FOo2.js";
import { t as DEFAULT_ACCOUNT_ID } from "../account-id-BuseNZr0.js";
import { t as getPluginRuntimeGatewayRequestScope } from "../gateway-request-scope-CTcXqSrd.js";
import { c as isBlockedHostnameOrIp } from "../ssrf-CKxNXzEA.js";
import { h as mapAllowFromEntries } from "../channel-config-helpers-CP9RBkAj.js";
import { n as formatPairingApproveHint } from "../helpers-CS5OE-XO.js";
import { n as emptyPluginConfigSchema } from "../config-schema-ByMpA8_M.js";
import { t as createChannelReplyPipeline } from "../channel-reply-pipeline-Bh3Tpm_u.js";
import { c as collectStatusIssuesFromLastError, d as createDefaultChannelRuntimeState, r as buildComputedAccountStatusSnapshot } from "../status-helpers-X5NGYozQ.js";
import { a as createFixedWindowRateLimiter } from "../webhook-memory-guards-CnlIasFU.js";
import { c as requestBodyErrorToText, o as readJsonBodyWithLimit } from "../http-body-35ouPyQ5.js";
import { t as createOptionalChannelSetupSurface } from "../channel-setup-C-4z27M0.js";
import { n as resolveInboundDirectDmAccessWithRuntime, t as createPreCryptoDirectDmAuthorizer } from "../direct-dm-access-BfJbJ7oa.js";
import { t as createDirectDmPreCryptoGuardPolicy } from "../direct-dm-guard-policy-iVfEE6fV.js";
import { t as dispatchInboundDirectDmWithRuntime } from "../direct-dm-DOaIVo31.js";
//#region src/plugin-sdk/nostr.ts
const nostrSetup = createOptionalChannelSetupSurface({
	channel: "nostr",
	label: "Nostr",
	npmSpec: "@openclaw/nostr",
	docsPath: "/channels/nostr"
});
const nostrSetupAdapter = nostrSetup.setupAdapter;
const nostrSetupWizard = nostrSetup.setupWizard;
//#endregion
export { DEFAULT_ACCOUNT_ID, MarkdownConfigSchema, buildChannelConfigSchema, buildComputedAccountStatusSnapshot, collectStatusIssuesFromLastError, createChannelReplyPipeline, createDefaultChannelRuntimeState, createDirectDmPreCryptoGuardPolicy, createFixedWindowRateLimiter, createPreCryptoDirectDmAuthorizer, dispatchInboundDirectDmWithRuntime, emptyPluginConfigSchema, formatPairingApproveHint, getPluginRuntimeGatewayRequestScope, isBlockedHostnameOrIp, mapAllowFromEntries, nostrSetupAdapter, nostrSetupWizard, readJsonBodyWithLimit, requestBodyErrorToText, resolveInboundDirectDmAccessWithRuntime };
