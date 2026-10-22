import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as createProviderApiKeyAuthMethod } from "../../provider-api-key-auth-CU5upneV.js";
import "../../provider-auth-api-key-DtIqfQNx.js";
import { t as buildImageGenerationProvider } from "../../image-generation-provider-C6dRoRI8.js";
//#region extensions/image-generation-internal/index.ts
const PROVIDER_ID = "image_generation";
var image_generation_internal_default = definePluginEntry({
	id: "image-generation-internal",
	name: "Image Generation",
	description: "Bundled internal image generation provider",
	register(api) {
		api.registerProvider({
			id: PROVIDER_ID,
			label: "Image Generation",
			docsPath: "/providers/image-generation",
			envVars: ["WQ_API_KEY"],
			auth: [createProviderApiKeyAuthMethod({
				providerId: PROVIDER_ID,
				methodId: "api-key",
				label: "Image Generation API key",
				hint: "Internal image generation API key",
				optionKey: "imageGenerationApiKey",
				flagName: "--image-generation-api-key",
				envVar: "WQ_API_KEY",
				promptMessage: "Enter Image Generation API key",
				expectedProviders: [PROVIDER_ID],
				wizard: {
					choiceId: "image-generation-api-key",
					choiceLabel: "Image Generation API key",
					choiceHint: "Internal image generation API key",
					groupId: "image_generation",
					groupLabel: "Image Generation",
					groupHint: "Internal image generation",
					onboardingScopes: ["image-generation"]
				}
			})]
		});
		api.registerImageGenerationProvider(buildImageGenerationProvider());
	}
});
//#endregion
export { image_generation_internal_default as default };
