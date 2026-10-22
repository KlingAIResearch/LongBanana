import { a as resolveSlackAccount, t as listEnabledSlackAccounts } from "./accounts-DJiceqJx.js";
import { n as isSlackInteractiveRepliesEnabled } from "./interactive-replies-CvLwrG1P.js";
import { createActionGate } from "openclaw/plugin-sdk/channel-actions";
import { extractToolSend } from "openclaw/plugin-sdk/tool-send";
import { Type } from "@sinclair/typebox";
//#region extensions/slack/src/message-actions.ts
function listSlackMessageActions(cfg, accountId) {
	const accounts = (accountId ? [resolveSlackAccount({
		cfg,
		accountId
	})] : listEnabledSlackAccounts(cfg)).filter((account) => account.enabled && account.botTokenSource !== "none");
	if (accounts.length === 0) return [];
	const isActionEnabled = (key, defaultValue = true) => {
		for (const account of accounts) if (createActionGate(account.actions ?? cfg.channels?.slack?.actions)(key, defaultValue)) return true;
		return false;
	};
	const actions = new Set(["send"]);
	if (isActionEnabled("reactions")) {
		actions.add("react");
		actions.add("reactions");
	}
	if (isActionEnabled("messages")) {
		actions.add("read");
		actions.add("edit");
		actions.add("delete");
		actions.add("download-file");
		actions.add("upload-file");
	}
	if (isActionEnabled("pins")) {
		actions.add("pin");
		actions.add("unpin");
		actions.add("list-pins");
	}
	if (isActionEnabled("memberInfo")) actions.add("member-info");
	if (isActionEnabled("emojiList")) actions.add("emoji-list");
	return Array.from(actions);
}
function extractSlackToolSend(args) {
	return extractToolSend(args, "sendMessage");
}
//#endregion
//#region extensions/slack/src/message-tool-schema.ts
function createSlackMessageToolBlocksSchema() {
	return Type.Array(Type.Object({}, {
		additionalProperties: true,
		description: "Slack Block Kit payload blocks (Slack only)."
	}));
}
//#endregion
//#region extensions/slack/src/message-tool-api.ts
function describeSlackMessageTool({ cfg, accountId }) {
	const actions = listSlackMessageActions(cfg, accountId);
	const capabilities = /* @__PURE__ */ new Set();
	if (actions.includes("send")) capabilities.add("blocks");
	if (isSlackInteractiveRepliesEnabled({
		cfg,
		accountId
	})) capabilities.add("interactive");
	return {
		actions,
		capabilities: Array.from(capabilities),
		schema: actions.includes("send") ? { properties: { blocks: Type.Optional(createSlackMessageToolBlocksSchema()) } } : null
	};
}
//#endregion
export { extractSlackToolSend as n, listSlackMessageActions as r, describeSlackMessageTool as t };
