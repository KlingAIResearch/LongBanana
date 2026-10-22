import "./zod-schema.core-gdcGSc89.js";
import "./config-schema-B5e-FOo2.js";
import "./channel-reply-pipeline-Bh3Tpm_u.js";
import { t as createOptionalChannelSetupSurface } from "./channel-setup-C-4z27M0.js";
//#region src/plugin-sdk/twitch.ts
const twitchSetup = createOptionalChannelSetupSurface({
	channel: "twitch",
	label: "Twitch",
	npmSpec: "@openclaw/twitch"
});
const twitchSetupAdapter = twitchSetup.setupAdapter;
const twitchSetupWizard = twitchSetup.setupWizard;
//#endregion
export { twitchSetupWizard as n, twitchSetupAdapter as t };
