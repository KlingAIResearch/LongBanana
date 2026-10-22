// Legacy shim for pre-tsdown update-cli imports.
import * as daemonCli from "../daemon-cli-B06lVrKc.js";
import * as daemonCliRunners0 from "../install.runtime-BQuj1caH.js";
import * as daemonCliRunners1 from "../lifecycle.runtime-6cKEOYTu.js";
import * as daemonCliRunners2 from "../status.runtime-BHBzmSlE.js";
export const registerDaemonCli = daemonCli.t;
export const runDaemonInstall = daemonCliRunners0.runDaemonInstall;
export const runDaemonRestart = daemonCliRunners1.runDaemonRestart;
export const runDaemonStart = daemonCliRunners1.runDaemonStart;
export const runDaemonStatus = daemonCliRunners2.runDaemonStatus;
export const runDaemonStop = daemonCliRunners1.runDaemonStop;
export const runDaemonUninstall = daemonCliRunners1.runDaemonUninstall;
