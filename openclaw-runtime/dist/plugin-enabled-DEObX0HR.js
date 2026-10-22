import { a as normalizePluginsConfig, o as resolveEffectiveEnableState } from "./config-state-Cf5IQiV0.js";
import "./browser-config-runtime-_jw2J4Tj.js";
import { o as stopOpenClawChrome } from "./chrome-DSsDA-iw.js";
import { n as listKnownProfileNames, t as createBrowserRouteContext } from "./server-context-CiOZ3LGx.js";
import { t as isPwAiLoaded } from "./pw-ai-state-B6hGh03L.js";
//#region extensions/browser/src/browser/server-lifecycle.ts
async function ensureExtensionRelayForProfiles(_params) {}
async function stopKnownBrowserProfiles(params) {
	const current = params.getState();
	if (!current) return;
	const ctx = createBrowserRouteContext({
		getState: params.getState,
		refreshConfigFromDisk: true
	});
	try {
		for (const name of listKnownProfileNames(current)) try {
			const runtime = current.profiles.get(name);
			if (runtime?.running) {
				await stopOpenClawChrome(runtime.running);
				runtime.running = null;
				continue;
			}
			await ctx.forProfile(name).stopRunningBrowser();
		} catch {}
	} catch (err) {
		params.onWarn(`openclaw browser stop failed: ${String(err)}`);
	}
}
//#endregion
//#region extensions/browser/src/browser/runtime-lifecycle.ts
async function createBrowserRuntimeState(params) {
	const state = {
		server: params.server ?? null,
		port: params.port,
		resolved: params.resolved,
		profiles: /* @__PURE__ */ new Map()
	};
	await ensureExtensionRelayForProfiles({
		resolved: params.resolved,
		onWarn: params.onWarn
	});
	return state;
}
async function stopBrowserRuntime(params) {
	if (!params.current) return;
	await stopKnownBrowserProfiles({
		getState: params.getState,
		onWarn: params.onWarn
	});
	if (params.closeServer && params.current.server) await new Promise((resolve) => {
		params.current?.server?.close(() => resolve());
	});
	params.clearState();
	if (!isPwAiLoaded()) return;
	try {
		await (await import("./pw-ai-DPzafj8o.js")).closePlaywrightBrowserConnection();
	} catch {}
}
//#endregion
//#region extensions/browser/src/plugin-enabled.ts
function isDefaultBrowserPluginEnabled(cfg) {
	return resolveEffectiveEnableState({
		id: "browser",
		origin: "bundled",
		config: normalizePluginsConfig(cfg.plugins),
		rootConfig: cfg,
		enabledByDefault: true
	}).enabled;
}
//#endregion
export { createBrowserRuntimeState as n, stopBrowserRuntime as r, isDefaultBrowserPluginEnabled as t };
