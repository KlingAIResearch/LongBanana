import { o as updateSessionStore } from "./store-BQPg58te.js";
import { n as mergeSessionEntry } from "./types-CtTGbjB5.js";
import { h as hasInternalRuntimeContext } from "./sanitize-user-facing-text-DQG1409e.js";
import { t as formatAgentInternalEventsForPrompt } from "./internal-events-DI7Flx3I.js";
//#region src/agents/command/attempt-execution.shared.ts
async function persistSessionEntry(params) {
	const persisted = await updateSessionStore(params.storePath, (store) => {
		const merged = mergeSessionEntry(store[params.sessionKey], params.entry);
		for (const field of params.clearedFields ?? []) if (!Object.hasOwn(params.entry, field)) Reflect.deleteProperty(merged, field);
		store[params.sessionKey] = merged;
		return merged;
	});
	params.sessionStore[params.sessionKey] = persisted;
}
function prependInternalEventContext(body, events) {
	if (hasInternalRuntimeContext(body)) return body;
	const renderedEvents = formatAgentInternalEventsForPrompt(events);
	if (!renderedEvents) return body;
	return [renderedEvents, body].filter(Boolean).join("\n\n");
}
//#endregion
export { prependInternalEventContext as n, persistSessionEntry as t };
