import { a as buildProviderToolCompatFamilyHooks } from "../../provider-tools-BEjp4Q9-.js";
import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as buildOpenAICodexCliBackend } from "../../cli-backend-BHKmgvHM.js";
import { t as buildOpenAIImageGenerationProvider } from "../../image-generation-provider-ompGUORp.js";
import { n as openaiCodexMediaUnderstandingProvider, r as openaiMediaUnderstandingProvider } from "../../media-understanding-provider-B0FEsZnc.js";
import { t as openAiMemoryEmbeddingProviderAdapter } from "../../memory-embedding-adapter-D8duMMoK.js";
import { t as buildOpenAICodexProviderPlugin } from "../../openai-codex-provider-DjFPtOL8.js";
import { t as buildOpenAIProvider } from "../../openai-provider-CeQiO97_.js";
import { a as resolveOpenAIPromptOverlayMode, o as resolveOpenAISystemPromptContribution } from "../../prompt-overlay-Cil_f9jB.js";
import { t as buildOpenAIRealtimeTranscriptionProvider } from "../../realtime-transcription-provider-DhVkSZBc.js";
import { t as buildOpenAIRealtimeVoiceProvider } from "../../realtime-voice-provider-CmZwGcUo.js";
import { t as buildOpenAISpeechProvider } from "../../speech-provider-DYv4M8KH.js";
import { t as buildOpenAIVideoGenerationProvider } from "../../video-generation-provider-203RJVZQ.js";
//#region extensions/openai/index.ts
var openai_default = definePluginEntry({
	id: "openai",
	name: "OpenAI Provider",
	description: "Bundled OpenAI provider plugins",
	register(api) {
		const promptOverlayMode = resolveOpenAIPromptOverlayMode(api.pluginConfig);
		const openAIToolCompatHooks = buildProviderToolCompatFamilyHooks("openai");
		const buildProviderWithPromptContribution = (provider) => ({
			...provider,
			...openAIToolCompatHooks,
			resolveSystemPromptContribution: (ctx) => resolveOpenAISystemPromptContribution({
				mode: promptOverlayMode,
				modelProviderId: provider.id,
				modelId: ctx.modelId
			})
		});
		api.registerCliBackend(buildOpenAICodexCliBackend());
		api.registerProvider(buildProviderWithPromptContribution(buildOpenAIProvider()));
		api.registerProvider(buildProviderWithPromptContribution(buildOpenAICodexProviderPlugin()));
		api.registerMemoryEmbeddingProvider(openAiMemoryEmbeddingProviderAdapter);
		api.registerImageGenerationProvider(buildOpenAIImageGenerationProvider());
		api.registerRealtimeTranscriptionProvider(buildOpenAIRealtimeTranscriptionProvider());
		api.registerRealtimeVoiceProvider(buildOpenAIRealtimeVoiceProvider());
		api.registerSpeechProvider(buildOpenAISpeechProvider());
		api.registerMediaUnderstandingProvider(openaiMediaUnderstandingProvider);
		api.registerMediaUnderstandingProvider(openaiCodexMediaUnderstandingProvider);
		api.registerVideoGenerationProvider(buildOpenAIVideoGenerationProvider());
	}
});
//#endregion
export { openai_default as default };
