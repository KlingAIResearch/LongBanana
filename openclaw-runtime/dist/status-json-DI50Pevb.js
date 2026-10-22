import { t as runStatusJsonCommand } from "./status-json-command-pa1Mg03H.js";
import { t as scanStatusJsonFast } from "./status.scan.fast-json-DBNGMtkk.js";
//#region src/commands/status-json.ts
async function statusJsonCommand(opts, runtime) {
	await runStatusJsonCommand({
		opts,
		runtime,
		scanStatusJsonFast,
		includeSecurityAudit: opts.all === true,
		suppressHealthErrors: true
	});
}
//#endregion
export { statusJsonCommand };
