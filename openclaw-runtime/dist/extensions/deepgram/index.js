import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as deepgramMediaUnderstandingProvider } from "../../media-understanding-provider-CSQKVxuC.js";
//#region extensions/deepgram/index.ts
var deepgram_default = definePluginEntry({
	id: "deepgram",
	name: "Deepgram Media Understanding",
	description: "Bundled Deepgram audio transcription provider",
	register(api) {
		api.registerMediaUnderstandingProvider(deepgramMediaUnderstandingProvider);
	}
});
//#endregion
export { deepgram_default as default };
