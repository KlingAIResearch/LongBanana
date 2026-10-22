import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { n as buildMinimaxPortalImageGenerationProvider, t as buildMinimaxImageGenerationProvider } from "../../image-generation-provider-BzzFtZKN.js";
import { n as minimaxPortalMediaUnderstandingProvider, t as minimaxMediaUnderstandingProvider } from "../../media-understanding-provider-Cq_p7Z2o.js";
import { t as buildMinimaxMusicGenerationProvider } from "../../music-generation-provider-BlL4I8qJ.js";
import { t as registerMinimaxProviders } from "../../provider-registration-tJZe3s4B.js";
import { t as buildMinimaxSpeechProvider } from "../../speech-provider-cIS5vJgE.js";
import { t as createMiniMaxWebSearchProvider } from "../../minimax-web-search-provider-CtmRdbVr.js";
import { t as buildMinimaxVideoGenerationProvider } from "../../video-generation-provider-BtojUUhx.js";
//#region extensions/minimax/index.ts
var minimax_default = definePluginEntry({
	id: "minimax",
	name: "MiniMax",
	description: "Bundled MiniMax API-key and OAuth provider plugin",
	register(api) {
		registerMinimaxProviders(api);
		api.registerMediaUnderstandingProvider(minimaxMediaUnderstandingProvider);
		api.registerMediaUnderstandingProvider(minimaxPortalMediaUnderstandingProvider);
		api.registerImageGenerationProvider(buildMinimaxImageGenerationProvider());
		api.registerImageGenerationProvider(buildMinimaxPortalImageGenerationProvider());
		api.registerMusicGenerationProvider(buildMinimaxMusicGenerationProvider());
		api.registerVideoGenerationProvider(buildMinimaxVideoGenerationProvider());
		api.registerSpeechProvider(buildMinimaxSpeechProvider());
		api.registerWebSearchProvider(createMiniMaxWebSearchProvider());
	}
});
//#endregion
export { minimax_default as default };
