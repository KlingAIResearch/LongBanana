import "./types.secrets-DbVQrBMp.js";
import "./config-schema-B5e-FOo2.js";
import "./registry-CZ7mm4Ua.js";
import "./zod-schema.providers-core-Bzyf_1rd.js";
import "./fetch-guard-BihRI978.js";
import "./common-B-eA4nK1.js";
import "./fetch-Ce2Ze2zc.js";
import { n as resolveChannelGroupRequireMention } from "./group-policy-Dx7o3q7A.js";
import "./setup-helpers-CXFAhexK.js";
import "./channel-policy-B_ra2Ydm.js";
import "./dm-policy-shared-CVrajwZr.js";
import "./setup-wizard-helpers-C3fKdzMA.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import "./channel-pairing-Cgn4Qxx9.js";
import "./status-helpers-X5NGYozQ.js";
import "./webhook-ingress-d3B1liDG.js";
import { t as createOptionalChannelSetupSurface } from "./channel-setup-C-4z27M0.js";
import "./web-media-D7dy9l-q.js";
import "./outbound-media-BhrhlrIy.js";
//#region src/plugin-sdk/googlechat.ts
function resolveGoogleChatGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "googlechat",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
const googlechatSetup = createOptionalChannelSetupSurface({
	channel: "googlechat",
	label: "Google Chat",
	npmSpec: "@openclaw/googlechat",
	docsPath: "/channels/googlechat"
});
const googlechatSetupAdapter = googlechatSetup.setupAdapter;
const googlechatSetupWizard = googlechatSetup.setupWizard;
//#endregion
export { googlechatSetupWizard as n, resolveGoogleChatGroupRequireMention as r, googlechatSetupAdapter as t };
