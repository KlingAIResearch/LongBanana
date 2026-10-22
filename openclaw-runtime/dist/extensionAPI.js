import { n as DEFAULT_MODEL, r as DEFAULT_PROVIDER } from "./defaults-Dg026tI0.js";
import { d as ensureAgentWorkspace } from "./workspace-DJgqEHO4.js";
import { b as resolveAgentWorkspaceDir, y as resolveAgentDir } from "./agent-scope-Dm0VAW-j.js";
import { x as resolveThinkingDefault } from "./model-selection-BbGKRLeC.js";
import { n as resolveAgentIdentity } from "./identity-BN5OQFTZ.js";
import { i as saveSessionStore } from "./store-BQPg58te.js";
import "./sessions-ULJtkV29.js";
import { i as resolveSessionFilePath, u as resolveStorePath } from "./paths-WKsTZdeA.js";
import { t as loadSessionStore } from "./store-load-RjC_NzkA.js";
import { t as runEmbeddedPiAgent } from "./pi-embedded-runner-Bi0nS2jW.js";
import { t as resolveAgentTimeoutMs } from "./timeout-CNguz_dQ.js";
import "./pi-embedded-BhXk4n4w.js";
//#region src/extensionAPI.ts
if (process.env.VITEST !== "true" && process.env.OPENCLAW_SUPPRESS_EXTENSION_API_WARNING !== "1") process.emitWarning("openclaw/extension-api is deprecated. Migrate to api.runtime.agent.* or focused openclaw/plugin-sdk/<subpath> imports. See https://docs.openclaw.ai/plugins/sdk-migration", {
	code: "OPENCLAW_EXTENSION_API_DEPRECATED",
	detail: "This compatibility bridge is temporary. Bundled plugins should use the injected plugin runtime instead of importing host-side agent helpers directly. Migration guide: https://docs.openclaw.ai/plugins/sdk-migration"
});
//#endregion
export { DEFAULT_MODEL, DEFAULT_PROVIDER, ensureAgentWorkspace, loadSessionStore, resolveAgentDir, resolveAgentIdentity, resolveAgentTimeoutMs, resolveAgentWorkspaceDir, resolveSessionFilePath, resolveStorePath, resolveThinkingDefault, runEmbeddedPiAgent, saveSessionStore };
