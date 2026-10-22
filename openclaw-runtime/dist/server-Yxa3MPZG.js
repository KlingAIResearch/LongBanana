import { t as createSubsystemLogger } from "./subsystem-Dk33jKDp.js";
import { a as loadConfig } from "./io-zyJwuhrD.js";
import { r as setBridgeAuthForPort, t as deleteBridgeAuthForPort } from "./bridge-auth-registry-BgZ3BZLz.js";
import "./chrome-DSsDA-iw.js";
import { r as registerBrowserRoutes, t as createBrowserRouteContext } from "./server-context-CiOZ3LGx.js";
import { n as resolveBrowserControlAuth, r as shouldAutoGenerateBrowserAuth, t as ensureBrowserControlAuth } from "./control-auth-aTLMVGdf.js";
import { t as resolveBrowserConfig } from "./config-DwcqVIQi.js";
import { n as installBrowserAuthMiddleware, r as installBrowserCommonMiddleware } from "./server-middleware-DwHOA6gZ.js";
import { n as createBrowserRuntimeState, r as stopBrowserRuntime, t as isDefaultBrowserPluginEnabled } from "./plugin-enabled-DEObX0HR.js";
import express from "express";
//#region extensions/browser/src/server.ts
let state = null;
const logServer = createSubsystemLogger("browser").child("server");
async function startBrowserControlServerFromConfig() {
	if (state) return state;
	const cfg = loadConfig();
	if (!isDefaultBrowserPluginEnabled(cfg)) return null;
	const resolved = resolveBrowserConfig(cfg.browser, cfg);
	if (!resolved.enabled) return null;
	let browserAuth = resolveBrowserControlAuth(cfg);
	let browserAuthBootstrapFailed = false;
	try {
		const ensured = await ensureBrowserControlAuth({ cfg });
		browserAuth = ensured.auth;
		if (ensured.generatedToken) logServer.info("No browser auth configured; generated browser control auth credential automatically.");
	} catch (err) {
		logServer.warn(`failed to auto-configure browser auth: ${String(err)}`);
		browserAuthBootstrapFailed = true;
	}
	const browserAuthRequired = browserAuthBootstrapFailed || shouldAutoGenerateBrowserAuth(process.env);
	const allowLegacyPasswordModeWithoutSecret = !browserAuthBootstrapFailed && cfg.gateway?.auth?.mode === "password" && !browserAuth.token && !browserAuth.password;
	if (browserAuthRequired && !allowLegacyPasswordModeWithoutSecret && !browserAuth.token && !browserAuth.password) {
		if (browserAuthBootstrapFailed) logServer.error("browser control startup aborted: authentication bootstrap failed and no fallback auth is configured.");
		else logServer.error("browser control startup aborted: no authentication configured.");
		return null;
	}
	const app = express();
	installBrowserCommonMiddleware(app);
	installBrowserAuthMiddleware(app, browserAuth);
	registerBrowserRoutes(app, createBrowserRouteContext({
		getState: () => state,
		refreshConfigFromDisk: true
	}));
	const port = resolved.controlPort;
	const server = await new Promise((resolve, reject) => {
		const s = app.listen(port, "127.0.0.1", () => resolve(s));
		s.once("error", reject);
	}).catch((err) => {
		logServer.error(`openclaw browser server failed to bind 127.0.0.1:${port}: ${String(err)}`);
		return null;
	});
	if (!server) return null;
	state = await createBrowserRuntimeState({
		server,
		port,
		resolved,
		onWarn: (message) => logServer.warn(message)
	});
	setBridgeAuthForPort(port, browserAuth);
	const authMode = browserAuth.token ? "token" : browserAuth.password ? "password" : "off";
	logServer.info(`Browser control listening on http://127.0.0.1:${port}/ (auth=${authMode})`);
	return state;
}
async function stopBrowserControlServer() {
	const current = state;
	if (current?.port) deleteBridgeAuthForPort(current.port);
	await stopBrowserRuntime({
		current,
		getState: () => state,
		clearState: () => {
			state = null;
		},
		closeServer: true,
		onWarn: (message) => logServer.warn(message)
	});
}
//#endregion
export { startBrowserControlServerFromConfig, stopBrowserControlServer };
