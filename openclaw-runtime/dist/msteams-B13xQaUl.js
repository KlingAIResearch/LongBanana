import "./utils-D5DtWkEu.js";
import "./types.secrets-DbVQrBMp.js";
import "./config-schema-B5e-FOo2.js";
import "./zod-schema.providers-core-Bzyf_1rd.js";
import "./file-lock-BmcrMV8d.js";
import "./tokens-HkZ7pDxX.js";
import "./mime-BcQn-bgb.js";
import "./ssrf-CKxNXzEA.js";
import "./fetch-guard-BihRI978.js";
import "./store-BnYV_Cgs.js";
import "./json-store-DMXCWMUe.js";
import "./dm-policy-shared-CVrajwZr.js";
import "./history-xZ340_AE.js";
import "./setup-wizard-helpers-C3fKdzMA.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import "./channel-pairing-Cgn4Qxx9.js";
import "./status-helpers-X5NGYozQ.js";
import "./http-body-35ouPyQ5.js";
import { t as createOptionalChannelSetupSurface } from "./channel-setup-C-4z27M0.js";
import "./inbound-reply-dispatch-Bm1FtH84.js";
import "./web-media-D7dy9l-q.js";
import "./outbound-media-BhrhlrIy.js";
import "./ssrf-policy-D0O6hx0Q.js";
import "./session-envelope-Ca7vFT9p.js";
//#region src/plugin-sdk/msteams.ts
const msteamsSetup = createOptionalChannelSetupSurface({
	channel: "msteams",
	label: "Microsoft Teams",
	npmSpec: "@openclaw/msteams",
	docsPath: "/channels/msteams"
});
const msteamsSetupWizard = msteamsSetup.setupWizard;
const msteamsSetupAdapter = msteamsSetup.setupAdapter;
//#endregion
export { msteamsSetupWizard as n, msteamsSetupAdapter as t };
