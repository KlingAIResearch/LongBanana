import { t as definePluginEntry } from "../../plugin-entry-C_x2qjuV.js";
import { n as createBraveWebSearchProvider } from "../../brave-web-search-provider-CwdJ_Vx-.js";
//#region extensions/brave/index.ts
var brave_default = definePluginEntry({
	id: "brave",
	name: "Brave Plugin",
	description: "Bundled Brave plugin",
	register(api) {
		api.registerWebSearchProvider(createBraveWebSearchProvider());
	}
});
//#endregion
export { brave_default as default };
