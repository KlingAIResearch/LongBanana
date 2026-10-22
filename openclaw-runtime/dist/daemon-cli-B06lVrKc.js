import { t as formatDocsLink } from "./links-CdeABZi6.js";
import { r as theme } from "./theme-Z35XKETL.js";
import { t as addGatewayServiceCommands } from "./register-service-commands-cyVn4w7S.js";
import "./install-Ba4_GlhK.js";
import "./lifecycle-CB4HNa-9.js";
import "./status-CE3HF_pv.js";
//#region src/cli/daemon-cli/register.ts
function registerDaemonCli(program) {
	addGatewayServiceCommands(program.command("daemon").description("Manage the Gateway service (launchd/systemd/schtasks)").addHelpText("after", () => `\n${theme.muted("Docs:")} ${formatDocsLink("/cli/gateway", "docs.openclaw.ai/cli/gateway")}\n`), { statusDescription: "Show service install status + probe the Gateway" });
}
//#endregion
export { registerDaemonCli as t };
