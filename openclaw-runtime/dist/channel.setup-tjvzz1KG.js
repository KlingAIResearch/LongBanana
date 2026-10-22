import { t as createZalouserPluginBase } from "./shared-Wb1aFLsc.js";
import { n as zalouserSetupAdapter } from "./setup-core-DTbaXwuQ.js";
import { t as zalouserSetupWizard } from "./setup-surface-CdS4rhbZ.js";
//#region extensions/zalouser/src/channel.setup.ts
const zalouserSetupPlugin = { ...createZalouserPluginBase({
	setupWizard: zalouserSetupWizard,
	setup: zalouserSetupAdapter
}) };
//#endregion
export { zalouserSetupPlugin as t };
