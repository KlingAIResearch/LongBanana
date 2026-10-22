import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { t as groqMediaUnderstandingProvider } from "../../media-understanding-provider-Cki_WxP9.js";
//#region extensions/groq/index.ts
var groq_default = definePluginEntry({
	id: "groq",
	name: "Groq Media Understanding",
	description: "Bundled Groq audio transcription provider",
	register(api) {
		api.registerMediaUnderstandingProvider(groqMediaUnderstandingProvider);
	}
});
//#endregion
export { groq_default as default };
