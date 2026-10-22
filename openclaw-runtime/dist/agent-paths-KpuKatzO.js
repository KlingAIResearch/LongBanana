import { m as resolveUserPath } from "./utils-D5DtWkEu.js";
import { _ as resolveStateDir } from "./paths-CT5Km_Zi.js";
import { t as DEFAULT_AGENT_ID } from "./session-key-ZJPu_0qD.js";
import path from "node:path";
//#region src/agents/agent-paths.ts
function resolveOpenClawAgentDir(env = process.env) {
	const override = env.OPENCLAW_AGENT_DIR?.trim() || env.PI_CODING_AGENT_DIR?.trim();
	if (override) return resolveUserPath(override, env);
	return resolveUserPath(path.join(resolveStateDir(env), "agents", DEFAULT_AGENT_ID, "agent"), env);
}
//#endregion
export { resolveOpenClawAgentDir as t };
