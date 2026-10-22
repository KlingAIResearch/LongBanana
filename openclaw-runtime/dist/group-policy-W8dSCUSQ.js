import { n as resolveChannelGroupRequireMention, r as resolveChannelGroupToolsPolicy } from "./group-policy-Dx7o3q7A.js";
import "./channel-policy-B_ra2Ydm.js";
//#region extensions/bluebubbles/src/group-policy.ts
function resolveBlueBubblesGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "bluebubbles",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
function resolveBlueBubblesGroupToolPolicy(params) {
	return resolveChannelGroupToolsPolicy({
		cfg: params.cfg,
		channel: "bluebubbles",
		groupId: params.groupId,
		accountId: params.accountId,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
}
//#endregion
export { resolveBlueBubblesGroupToolPolicy as n, resolveBlueBubblesGroupRequireMention as t };
