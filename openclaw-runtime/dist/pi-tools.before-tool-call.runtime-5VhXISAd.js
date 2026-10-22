import { n as getDiagnosticSessionState } from "./diagnostic-session-state-TT8JdFIE.js";
import { c as logToolLoopAction } from "./diagnostic-lUXhCOnt.js";
import { n as recordToolCall, r as recordToolCallOutcome, t as detectToolCallLoop } from "./tool-loop-detection-v9fjXQkD.js";
//#region src/agents/pi-tools.before-tool-call.runtime.ts
const beforeToolCallRuntime = {
	getDiagnosticSessionState,
	logToolLoopAction,
	detectToolCallLoop,
	recordToolCall,
	recordToolCallOutcome
};
//#endregion
export { beforeToolCallRuntime };
