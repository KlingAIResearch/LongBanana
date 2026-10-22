import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { n as createPerplexityWebSearchProvider } from "../../perplexity-web-search-provider-DIR4-dTW.js";
//#region extensions/perplexity/index.ts
var perplexity_default = definePluginEntry({
	id: "perplexity",
	name: "Perplexity Plugin",
	description: "Bundled Perplexity plugin",
	register(api) {
		api.registerWebSearchProvider(createPerplexityWebSearchProvider());
	}
});
//#endregion
export { perplexity_default as default };
