import { DEFAULT_BEDROCK_EMBEDDING_MODEL, createBedrockEmbeddingProvider } from "./embedding-provider.js";
import { isMissingEmbeddingApiKeyError } from "openclaw/plugin-sdk/memory-core-host-engine-embeddings";
//#region extensions/amazon-bedrock/memory-embedding-adapter.ts
const bedrockMemoryEmbeddingProviderAdapter = {
	id: "bedrock",
	defaultModel: DEFAULT_BEDROCK_EMBEDDING_MODEL,
	transport: "remote",
	authProviderId: "amazon-bedrock",
	autoSelectPriority: 60,
	allowExplicitWhenConfiguredAuto: true,
	shouldContinueAutoSelection: isMissingEmbeddingApiKeyError,
	create: async (options) => {
		const { provider, client } = await createBedrockEmbeddingProvider({
			...options,
			provider: "bedrock",
			fallback: "none"
		});
		return {
			provider,
			runtime: {
				id: "bedrock",
				cacheKeyData: {
					provider: "bedrock",
					region: client.region,
					model: client.model,
					dimensions: client.dimensions
				}
			}
		};
	}
};
//#endregion
export { bedrockMemoryEmbeddingProviderAdapter };
