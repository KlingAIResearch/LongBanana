import { p as resolveHomeDir } from "./utils-D5DtWkEu.js";
import { l as readConfigFileSnapshot } from "./io-zyJwuhrD.js";
import { n as formatConfigIssueLines } from "./issue-format-CDWMnxNu.js";
import { t as note } from "./note-Bs7Em1w9.js";
import { n as noteIncludeConfinementWarning } from "./doctor-config-analysis-C5yRUMAD.js";
import path from "node:path";
import fs from "node:fs/promises";
//#region src/commands/doctor-config-preflight.ts
async function maybeMigrateLegacyConfig() {
	const changes = [];
	const home = resolveHomeDir();
	if (!home) return changes;
	const targetDir = path.join(home, ".openclaw");
	const targetPath = path.join(targetDir, "openclaw.json");
	try {
		await fs.access(targetPath);
		return changes;
	} catch {}
	const legacyCandidates = [path.join(home, ".clawdbot", "clawdbot.json")];
	let legacyPath = null;
	for (const candidate of legacyCandidates) try {
		await fs.access(candidate);
		legacyPath = candidate;
		break;
	} catch {}
	if (!legacyPath) return changes;
	await fs.mkdir(targetDir, { recursive: true });
	try {
		await fs.copyFile(legacyPath, targetPath, fs.constants.COPYFILE_EXCL);
		changes.push(`Migrated legacy config: ${legacyPath} -> ${targetPath}`);
	} catch {}
	return changes;
}
async function runDoctorConfigPreflight(options = {}) {
	if (options.migrateState !== false) {
		const { autoMigrateLegacyStateDir } = await import("./doctor-state-migrations-DBr-YtHl.js");
		const stateDirResult = await autoMigrateLegacyStateDir({ env: process.env });
		if (stateDirResult.changes.length > 0) note(stateDirResult.changes.map((entry) => `- ${entry}`).join("\n"), "Doctor changes");
		if (stateDirResult.warnings.length > 0) note(stateDirResult.warnings.map((entry) => `- ${entry}`).join("\n"), "Doctor warnings");
	}
	if (options.migrateLegacyConfig !== false) {
		const legacyConfigChanges = await maybeMigrateLegacyConfig();
		if (legacyConfigChanges.length > 0) note(legacyConfigChanges.map((entry) => `- ${entry}`).join("\n"), "Doctor changes");
	}
	const snapshot = await readConfigFileSnapshot();
	const invalidConfigNote = options.invalidConfigNote ?? "Config invalid; doctor will run with best-effort config.";
	if (invalidConfigNote && snapshot.exists && !snapshot.valid && snapshot.legacyIssues.length === 0) {
		note(invalidConfigNote, "Config");
		noteIncludeConfinementWarning(snapshot);
	}
	const warnings = snapshot.warnings ?? [];
	if (warnings.length > 0) note(formatConfigIssueLines(warnings, "-").join("\n"), "Config warnings");
	return {
		snapshot,
		baseConfig: snapshot.sourceConfig ?? snapshot.config ?? {}
	};
}
//#endregion
export { runDoctorConfigPreflight as t };
