import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as createProviderApiKeyAuthMethod } from "../../provider-api-key-auth-CU5upneV.js";
import "../../provider-auth-api-key-DtIqfQNx.js";
import { n as buildFalImageGenerationProvider } from "../../image-generation-provider-DhVEdr6D2.js";
import { n as applyFalConfig, t as FAL_DEFAULT_IMAGE_MODEL_REF } from "../../onboard-DBMtlt-S.js";
import { n as buildFalVideoGenerationProvider } from "../../video-generation-provider-CJZ6-PnS2.js";
//#region extensions/fal/index.ts
const PROVIDER_ID = "fal";
var fal_default = definePluginEntry({
	id: PROVIDER_ID,
	name: "fal Provider",
	description: "Bundled fal image and video generation provider",
	register(api) {
		api.registerProvider({
			id: PROVIDER_ID,
			label: "fal",
			docsPath: "/providers/models",
			envVars: ["FAL_KEY"],
			auth: [createProviderApiKeyAuthMethod({
				providerId: PROVIDER_ID,
				methodId: "api-key",
				label: "fal API key",
				hint: "Image and video generation API key",
				optionKey: "falApiKey",
				flagName: "--fal-api-key",
				envVar: "FAL_KEY",
				promptMessage: "Enter fal API key",
				defaultModel: FAL_DEFAULT_IMAGE_MODEL_REF,
				expectedProviders: ["fal"],
				applyConfig: (cfg) => applyFalConfig(cfg),
				wizard: {
					choiceId: "fal-api-key",
					choiceLabel: "fal API key",
					choiceHint: "Image and video generation API key",
					groupId: "fal",
					groupLabel: "fal",
					groupHint: "Image and video generation",
					onboardingScopes: ["image-generation"]
				}
			})]
		});
		api.registerImageGenerationProvider(buildFalImageGenerationProvider());
		api.registerVideoGenerationProvider(buildFalVideoGenerationProvider());
	}
});
//#endregion
export { fal_default as default };
