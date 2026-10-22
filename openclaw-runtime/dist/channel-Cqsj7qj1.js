import { i as normalizeLowercaseStringOrEmpty$1, s as normalizeOptionalString$2 } from "./string-coerce-BUSzWgUA.js";
import { t as formatDocsLink } from "./links-CdeABZi6.js";
import { o as isSecretRef } from "./types.secrets-DbVQrBMp.js";
import { r as buildChannelConfigSchema } from "./config-schema-B5e-FOo2.js";
import { n as normalizeAccountId, t as DEFAULT_ACCOUNT_ID } from "./account-id-BuseNZr0.js";
import { n as GoogleChatConfigSchema } from "./zod-schema.providers-core-Bzyf_1rd.js";
import { n as safeParseWithSchema, t as safeParseJsonWithSchema } from "./zod-parse-Xlo06-9H.js";
import { t as resolveAccountEntry } from "./account-lookup-CP-ZGR_l.js";
import { i as createLazyRuntimeNamedExport } from "./lazy-runtime-C7CyZdwe.js";
import { c as jsonResult, d as readNumberParam, f as readReactionParams, h as readStringParam, i as createActionGate } from "./common-B-eA4nK1.js";
import { n as fetchRemoteMedia } from "./fetch-Ce2Ze2zc.js";
import { n as resolveChannelGroupRequireMention } from "./group-policy-Dx7o3q7A.js";
import { n as missingTargetError } from "./target-errors-DzURL9hd.js";
import { c as createScopedChannelConfigAdapter, t as adaptScopedAccountAccessor } from "./channel-config-helpers-CP9RBkAj.js";
import "./text-runtime-BZ19VEh4.js";
import { n as describeAccountSnapshot, s as resolveMergedAccountConfig, t as createAccountListHelpers } from "./account-helpers-B8-OixoH.js";
import { a as createSetupInputPresenceValidator, i as createPatchedAccountSetupAdapter, n as applySetupAccountConfigPatch, s as migrateBaseNameToDefaultAccount } from "./setup-helpers-CXFAhexK.js";
import { r as createChatChannelPlugin } from "./core-BRrvsWXZ.js";
import "./channel-core-DVxr0qAm.js";
import "./secret-input-U_-hh94N.js";
import { r as runPassiveAccountLifecycle, t as createAccountStatusSink } from "./channel-lifecycle.core-BN_WDHzw.js";
import { n as formatNormalizedAllowFromEntries } from "./allow-from-BsldHaeo.js";
import { g as createAllowlistProviderOpenWarningCollector, n as createDangerousNameMatchingMutableAllowlistWarningCollector, p as composeAccountWarningCollectors } from "./channel-policy-B_ra2Ydm.js";
import { t as createChannelDirectoryAdapter } from "./directory-runtime-C7pqnHTl.js";
import { f as listResolvedDirectoryGroupEntriesFromMapKeys, p as listResolvedDirectoryUserEntriesFromAllowFrom } from "./directory-config-helpers-DqEd74G_.js";
import { t as resolveChannelMediaMaxBytes } from "./media-limits-DUiU2W8d.js";
import { Q as splitSetupEntries, d as createPromptParsedAllowFromForAccount, f as createStandardChannelSetupStatus, t as addWildcardAllowFrom, v as mergeAllowFromEntries } from "./setup-wizard-helpers-C3fKdzMA.js";
import { t as PAIRING_APPROVED_MESSAGE } from "./pairing-message-0jf93unW.js";
import { d as createDefaultChannelRuntimeState, u as createComputedAccountStatusAdapter } from "./status-helpers-X5NGYozQ.js";
import { t as extractToolSend } from "./tool-send-cki5_wu2.js";
import "./setup-C1V4nBvJ.js";
import "./setup-runtime-D_drW-fM.js";
import { t as resolveApprovalApprovers } from "./approval-approvers-CDsFmxtw.js";
import { t as createResolvedApproverActionAuthAdapter } from "./approval-auth-helpers-DSoDzyD1.js";
import { t as loadOutboundMediaFromUrl } from "./outbound-media-BhrhlrIy.js";
import { t as sanitizeForPlainText } from "./sanitize-text-BDF9aTzQ.js";
import "./outbound-runtime-CnhnQrg_.js";
import { t as chunkTextForOutbound } from "./text-chunking-DFXq7qu-.js";
import "./account-resolution-8VBJ03iF.js";
import { n as buildPassiveProbedChannelStatusSummary } from "./extension-shared-Cm3_PG-_.js";
import "./channel-actions-DkD19cHj.js";
import "./channel-lifecycle-C8Ly-mbq.js";
import { t as getGoogleChatRuntime } from "./runtime-api-w0xOkUIz.js";
import { a as findGoogleChatDirectMessage, c as sendGoogleChatMessage, o as listGoogleChatReactions, r as deleteGoogleChatReaction, t as createGoogleChatReaction, u as uploadGoogleChatAttachment } from "./api-kP-H-1fd.js";
import { n as collectRuntimeConfigAssignments, r as secretTargetRegistryEntries } from "./secret-contract-DfpzQtwj.js";
import { z } from "zod";
//#region extensions/googlechat/src/accounts.ts
const ENV_SERVICE_ACCOUNT$1 = "GOOGLE_CHAT_SERVICE_ACCOUNT";
const ENV_SERVICE_ACCOUNT_FILE$1 = "GOOGLE_CHAT_SERVICE_ACCOUNT_FILE";
const JsonRecordSchema = z.record(z.string(), z.unknown());
function normalizeOptionalString$1(value) {
	if (typeof value !== "string") return;
	const trimmed = value.trim();
	return trimmed ? trimmed : void 0;
}
const { listAccountIds: listGoogleChatAccountIds, resolveDefaultAccountId: resolveDefaultGoogleChatAccountId } = createAccountListHelpers("googlechat");
function mergeGoogleChatAccountConfig(cfg, accountId) {
	const raw = cfg.channels?.["googlechat"] ?? {};
	const base = resolveMergedAccountConfig({
		channelConfig: raw,
		accounts: raw.accounts,
		accountId,
		omitKeys: ["defaultAccount"]
	});
	const defaultAccountConfig = resolveAccountEntry(raw.accounts, "default") ?? {};
	if (accountId === "default") return base;
	const { enabled: _ignoredEnabled, dangerouslyAllowNameMatching: _ignoredDangerouslyAllowNameMatching, serviceAccount: _ignoredServiceAccount, serviceAccountRef: _ignoredServiceAccountRef, serviceAccountFile: _ignoredServiceAccountFile, ...defaultAccountShared } = defaultAccountConfig;
	return {
		...defaultAccountShared,
		...base
	};
}
function parseServiceAccount(value) {
	if (isSecretRef(value)) return null;
	if (typeof value === "string") {
		const trimmed = value.trim();
		if (!trimmed) return null;
		return safeParseJsonWithSchema(JsonRecordSchema, trimmed);
	}
	return safeParseWithSchema(JsonRecordSchema, value);
}
function resolveCredentialsFromConfig(params) {
	const { account, accountId } = params;
	const inline = parseServiceAccount(account.serviceAccount);
	if (inline) return {
		credentials: inline,
		source: "inline"
	};
	if (isSecretRef(account.serviceAccount)) throw new Error(`channels.googlechat.accounts.${accountId}.serviceAccount: unresolved SecretRef "${account.serviceAccount.source}:${account.serviceAccount.provider}:${account.serviceAccount.id}". Resolve this command against an active gateway runtime snapshot before reading it.`);
	if (isSecretRef(account.serviceAccountRef)) throw new Error(`channels.googlechat.accounts.${accountId}.serviceAccount: unresolved SecretRef "${account.serviceAccountRef.source}:${account.serviceAccountRef.provider}:${account.serviceAccountRef.id}". Resolve this command against an active gateway runtime snapshot before reading it.`);
	const file = normalizeOptionalString$1(account.serviceAccountFile);
	if (file) return {
		credentialsFile: file,
		source: "file"
	};
	if (accountId === "default") {
		const envJson = process.env[ENV_SERVICE_ACCOUNT$1];
		const envInline = parseServiceAccount(envJson);
		if (envInline) return {
			credentials: envInline,
			source: "env"
		};
		const envFile = normalizeOptionalString$1(process.env[ENV_SERVICE_ACCOUNT_FILE$1]);
		if (envFile) return {
			credentialsFile: envFile,
			source: "env"
		};
	}
	return { source: "none" };
}
function resolveGoogleChatAccount(params) {
	const accountId = normalizeAccountId(params.accountId ?? params.cfg.channels?.["googlechat"]?.defaultAccount);
	const baseEnabled = params.cfg.channels?.["googlechat"]?.enabled !== false;
	const merged = mergeGoogleChatAccountConfig(params.cfg, accountId);
	const accountEnabled = merged.enabled !== false;
	const enabled = baseEnabled && accountEnabled;
	const credentials = resolveCredentialsFromConfig({
		accountId,
		account: merged
	});
	return {
		accountId,
		name: normalizeOptionalString$1(merged.name),
		enabled,
		config: merged,
		credentialSource: credentials.source,
		credentials: credentials.credentials,
		credentialsFile: credentials.credentialsFile
	};
}
function listEnabledGoogleChatAccounts(cfg) {
	return listGoogleChatAccountIds(cfg).map((accountId) => resolveGoogleChatAccount({
		cfg,
		accountId
	})).filter((account) => account.enabled);
}
//#endregion
//#region extensions/googlechat/src/targets.ts
function normalizeLowercaseStringOrEmpty(value) {
	return typeof value === "string" ? value.trim().toLowerCase() : "";
}
function normalizeGoogleChatTarget(raw) {
	const trimmed = raw?.trim();
	if (!trimmed) return;
	const normalized = trimmed.replace(/^(googlechat|google-chat|gchat):/i, "").replace(/^user:(users\/)?/i, "users/").replace(/^space:(spaces\/)?/i, "spaces/");
	if (isGoogleChatUserTarget(normalized)) {
		const suffix = normalized.slice(6);
		return suffix.includes("@") ? `users/${normalizeLowercaseStringOrEmpty(suffix)}` : normalized;
	}
	if (isGoogleChatSpaceTarget(normalized)) return normalized;
	if (normalized.includes("@")) return `users/${normalizeLowercaseStringOrEmpty(normalized)}`;
	return normalized;
}
function isGoogleChatUserTarget(value) {
	return normalizeLowercaseStringOrEmpty(value).startsWith("users/");
}
function isGoogleChatSpaceTarget(value) {
	return normalizeLowercaseStringOrEmpty(value).startsWith("spaces/");
}
function stripMessageSuffix(target) {
	const index = target.indexOf("/messages/");
	if (index === -1) return target;
	return target.slice(0, index);
}
async function resolveGoogleChatOutboundSpace(params) {
	const normalized = normalizeGoogleChatTarget(params.target);
	if (!normalized) throw new Error("Missing Google Chat target.");
	const base = stripMessageSuffix(normalized);
	if (isGoogleChatSpaceTarget(base)) return base;
	if (isGoogleChatUserTarget(base)) {
		const dm = await findGoogleChatDirectMessage({
			account: params.account,
			userName: base
		});
		if (!dm?.name) throw new Error(`No Google Chat DM found for ${base}`);
		return dm.name;
	}
	return base;
}
//#endregion
//#region extensions/googlechat/src/actions.ts
const providerId = "googlechat";
function listEnabledAccounts(cfg) {
	return listEnabledGoogleChatAccounts(cfg).filter((account) => account.enabled && account.credentialSource !== "none");
}
function isReactionsEnabled(accounts) {
	for (const account of accounts) if (createActionGate(account.config.actions)("reactions")) return true;
	return false;
}
function resolveAppUserNames(account) {
	return new Set(["users/app", account.config.botUser?.trim()].filter(Boolean));
}
async function loadGoogleChatActionMedia(params) {
	const runtime = getGoogleChatRuntime();
	return /^https?:\/\//i.test(params.mediaUrl) ? await runtime.channel.media.fetchRemoteMedia({
		url: params.mediaUrl,
		maxBytes: params.maxBytes
	}) : await loadOutboundMediaFromUrl(params.mediaUrl, {
		maxBytes: params.maxBytes,
		mediaAccess: params.mediaAccess,
		mediaLocalRoots: params.mediaLocalRoots,
		mediaReadFile: params.mediaReadFile
	});
}
const googlechatMessageActions = {
	describeMessageTool: ({ cfg, accountId }) => {
		const accounts = accountId ? [resolveGoogleChatAccount({
			cfg,
			accountId
		})].filter((account) => account.enabled && account.credentialSource !== "none") : listEnabledAccounts(cfg);
		if (accounts.length === 0) return null;
		const actions = /* @__PURE__ */ new Set([]);
		actions.add("send");
		actions.add("upload-file");
		if (isReactionsEnabled(accounts)) {
			actions.add("react");
			actions.add("reactions");
		}
		return { actions: Array.from(actions) };
	},
	extractToolSend: ({ args }) => {
		return extractToolSend(args, "sendMessage");
	},
	handleAction: async ({ action, params, cfg, accountId, mediaAccess, mediaLocalRoots, mediaReadFile }) => {
		const account = resolveGoogleChatAccount({
			cfg,
			accountId
		});
		if (account.credentialSource === "none") throw new Error("Google Chat credentials are missing.");
		if (action === "send" || action === "upload-file") {
			const to = readStringParam(params, "to", { required: true });
			const content = readStringParam(params, "message", {
				required: action === "send",
				allowEmpty: true
			}) ?? readStringParam(params, "initialComment", { allowEmpty: true }) ?? "";
			const mediaUrl = readStringParam(params, "media", { trim: false }) ?? readStringParam(params, "filePath", { trim: false }) ?? readStringParam(params, "path", { trim: false });
			const threadId = readStringParam(params, "threadId") ?? readStringParam(params, "replyTo");
			const space = await resolveGoogleChatOutboundSpace({
				account,
				target: to
			});
			if (mediaUrl) {
				const loaded = await loadGoogleChatActionMedia({
					mediaUrl,
					maxBytes: (account.config.mediaMaxMb ?? 20) * 1024 * 1024,
					mediaAccess,
					mediaLocalRoots,
					mediaReadFile
				});
				const uploadFileName = readStringParam(params, "filename") ?? readStringParam(params, "title") ?? loaded.fileName ?? "attachment";
				const upload = await uploadGoogleChatAttachment({
					account,
					space,
					filename: uploadFileName,
					buffer: loaded.buffer,
					contentType: loaded.contentType
				});
				await sendGoogleChatMessage({
					account,
					space,
					text: content,
					thread: threadId ?? void 0,
					attachments: upload.attachmentUploadToken ? [{
						attachmentUploadToken: upload.attachmentUploadToken,
						contentName: uploadFileName
					}] : void 0
				});
				return jsonResult({
					ok: true,
					to: space
				});
			}
			if (action === "upload-file") throw new Error("upload-file requires media, filePath, or path");
			await sendGoogleChatMessage({
				account,
				space,
				text: content,
				thread: threadId ?? void 0
			});
			return jsonResult({
				ok: true,
				to: space
			});
		}
		if (action === "react") {
			const messageName = readStringParam(params, "messageId", { required: true });
			const { emoji, remove, isEmpty } = readReactionParams(params, { removeErrorMessage: "Emoji is required to remove a Google Chat reaction." });
			if (remove || isEmpty) {
				const reactions = await listGoogleChatReactions({
					account,
					messageName
				});
				const appUsers = resolveAppUserNames(account);
				const toRemove = reactions.filter((reaction) => {
					const userName = reaction.user?.name?.trim();
					if (appUsers.size > 0 && !appUsers.has(userName ?? "")) return false;
					if (emoji) return reaction.emoji?.unicode === emoji;
					return true;
				});
				for (const reaction of toRemove) {
					if (!reaction.name) continue;
					await deleteGoogleChatReaction({
						account,
						reactionName: reaction.name
					});
				}
				return jsonResult({
					ok: true,
					removed: toRemove.length
				});
			}
			return jsonResult({
				ok: true,
				reaction: await createGoogleChatReaction({
					account,
					messageName,
					emoji
				})
			});
		}
		if (action === "reactions") return jsonResult({
			ok: true,
			reactions: await listGoogleChatReactions({
				account,
				messageName: readStringParam(params, "messageId", { required: true }),
				limit: readNumberParam(params, "limit", { integer: true }) ?? void 0
			})
		});
		throw new Error(`Action ${action} is not supported for provider ${providerId}.`);
	}
};
//#endregion
//#region extensions/googlechat/src/approval-auth.ts
function normalizeGoogleChatApproverId(value) {
	const normalized = normalizeGoogleChatTarget(String(value));
	if (!normalized || !isGoogleChatUserTarget(normalized)) return;
	const suffix = normalizeLowercaseStringOrEmpty$1(normalized.slice(6));
	if (!suffix || suffix.includes("@")) return;
	return `users/${suffix}`;
}
const googleChatApprovalAuth = createResolvedApproverActionAuthAdapter({
	channelLabel: "Google Chat",
	resolveApprovers: ({ cfg, accountId }) => {
		const account = resolveGoogleChatAccount({
			cfg,
			accountId
		}).config;
		return resolveApprovalApprovers({
			allowFrom: account.dm?.allowFrom,
			defaultTo: account.defaultTo,
			normalizeApprover: normalizeGoogleChatApproverId
		});
	},
	normalizeSenderId: (value) => normalizeGoogleChatApproverId(value)
});
//#endregion
//#region extensions/googlechat/src/group-policy.ts
function resolveGoogleChatGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "googlechat",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
//#endregion
//#region extensions/googlechat/src/channel.adapters.ts
const loadGoogleChatChannelRuntime$2 = createLazyRuntimeNamedExport(() => import("./channel.runtime-DkProO76.js"), "googleChatChannelRuntime");
const formatAllowFromEntry = (entry) => normalizeLowercaseStringOrEmpty$1(entry.trim().replace(/^(googlechat|google-chat|gchat):/i, "").replace(/^user:/i, "").replace(/^users\//i, ""));
const collectGoogleChatSecurityWarnings = composeAccountWarningCollectors(createAllowlistProviderOpenWarningCollector({
	providerConfigPresent: (cfg) => cfg.channels?.googlechat !== void 0,
	resolveGroupPolicy: (account) => account.config.groupPolicy,
	buildOpenWarning: {
		surface: "Google Chat spaces",
		openBehavior: "allows any space to trigger (mention-gated)",
		remediation: "Set channels.googlechat.groupPolicy=\"allowlist\" and configure channels.googlechat.groups"
	}
}), (account) => account.config.dm?.policy === "open" && "- Google Chat DMs are open to anyone. Set channels.googlechat.dm.policy=\"pairing\" or \"allowlist\".");
const googlechatGroupsAdapter = { resolveRequireMention: resolveGoogleChatGroupRequireMention };
const googlechatDirectoryAdapter = createChannelDirectoryAdapter({
	listPeers: async (params) => listResolvedDirectoryUserEntriesFromAllowFrom({
		...params,
		resolveAccount: adaptScopedAccountAccessor(resolveGoogleChatAccount),
		resolveAllowFrom: (account) => account.config.dm?.allowFrom,
		normalizeId: (entry) => normalizeGoogleChatTarget(entry) ?? entry
	}),
	listGroups: async (params) => listResolvedDirectoryGroupEntriesFromMapKeys({
		...params,
		resolveAccount: adaptScopedAccountAccessor(resolveGoogleChatAccount),
		resolveGroups: (account) => account.config.groups
	})
});
const googlechatSecurityAdapter = {
	dm: {
		channelKey: "googlechat",
		resolvePolicy: (account) => account.config.dm?.policy,
		resolveAllowFrom: (account) => account.config.dm?.allowFrom,
		allowFromPathSuffix: "dm.",
		normalizeEntry: (raw) => formatAllowFromEntry(raw)
	},
	collectWarnings: collectGoogleChatSecurityWarnings
};
const googlechatThreadingAdapter = { scopedAccountReplyToMode: {
	resolveAccount: (cfg, accountId) => resolveGoogleChatAccount({
		cfg,
		accountId
	}),
	resolveReplyToMode: (account, _chatType) => account.config.replyToMode,
	fallback: "off"
} };
const googlechatPairingTextAdapter = {
	idLabel: "googlechatUserId",
	message: PAIRING_APPROVED_MESSAGE,
	normalizeAllowEntry: (entry) => formatAllowFromEntry(entry),
	notify: async ({ cfg, id, message, accountId }) => {
		const account = resolveGoogleChatAccount({
			cfg,
			accountId
		});
		if (account.credentialSource === "none") return;
		const user = normalizeGoogleChatTarget(id) ?? id;
		const space = await resolveGoogleChatOutboundSpace({
			account,
			target: isGoogleChatUserTarget(user) ? user : `users/${user}`
		});
		const { sendGoogleChatMessage } = await loadGoogleChatChannelRuntime$2();
		await sendGoogleChatMessage({
			account,
			space,
			text: message
		});
	}
};
const googlechatOutboundAdapter = {
	base: {
		deliveryMode: "direct",
		chunker: chunkTextForOutbound,
		chunkerMode: "markdown",
		textChunkLimit: 4e3,
		sanitizeText: ({ text }) => sanitizeForPlainText(text),
		resolveTarget: ({ to }) => {
			const trimmed = normalizeOptionalString$2(to) ?? "";
			if (trimmed) {
				const normalized = normalizeGoogleChatTarget(trimmed);
				if (!normalized) return {
					ok: false,
					error: missingTargetError("Google Chat", "<spaces/{space}|users/{user}>")
				};
				return {
					ok: true,
					to: normalized
				};
			}
			return {
				ok: false,
				error: missingTargetError("Google Chat", "<spaces/{space}|users/{user}>")
			};
		}
	},
	attachedResults: {
		channel: "googlechat",
		sendText: async ({ cfg, to, text, accountId, replyToId, threadId }) => {
			const account = resolveGoogleChatAccount({
				cfg,
				accountId
			});
			const space = await resolveGoogleChatOutboundSpace({
				account,
				target: to
			});
			const thread = typeof threadId === "number" ? String(threadId) : threadId ?? replyToId ?? void 0;
			const { sendGoogleChatMessage } = await loadGoogleChatChannelRuntime$2();
			return {
				messageId: (await sendGoogleChatMessage({
					account,
					space,
					text,
					thread
				}))?.messageName ?? "",
				chatId: space
			};
		},
		sendMedia: async ({ cfg, to, text, mediaUrl, mediaAccess, mediaLocalRoots, mediaReadFile, accountId, replyToId, threadId }) => {
			if (!mediaUrl) throw new Error("Google Chat mediaUrl is required.");
			const account = resolveGoogleChatAccount({
				cfg,
				accountId
			});
			const space = await resolveGoogleChatOutboundSpace({
				account,
				target: to
			});
			const thread = typeof threadId === "number" ? String(threadId) : threadId ?? replyToId ?? void 0;
			const effectiveMaxBytes = resolveChannelMediaMaxBytes({
				cfg,
				resolveChannelLimitMb: ({ cfg, accountId }) => (cfg.channels?.googlechat)?.accounts?.[accountId]?.mediaMaxMb ?? (cfg.channels?.googlechat)?.mediaMaxMb,
				accountId
			}) ?? (account.config.mediaMaxMb ?? 20) * 1024 * 1024;
			const loaded = /^https?:\/\//i.test(mediaUrl) ? await fetchRemoteMedia({
				url: mediaUrl,
				maxBytes: effectiveMaxBytes
			}) : await loadOutboundMediaFromUrl(mediaUrl, {
				maxBytes: effectiveMaxBytes,
				mediaAccess,
				mediaLocalRoots,
				mediaReadFile
			});
			const { sendGoogleChatMessage, uploadGoogleChatAttachment } = await loadGoogleChatChannelRuntime$2();
			const upload = await uploadGoogleChatAttachment({
				account,
				space,
				filename: loaded.fileName ?? "attachment",
				buffer: loaded.buffer,
				contentType: loaded.contentType
			});
			return {
				messageId: (await sendGoogleChatMessage({
					account,
					space,
					text,
					thread,
					attachments: upload.attachmentUploadToken ? [{
						attachmentUploadToken: upload.attachmentUploadToken,
						contentName: loaded.fileName
					}] : void 0
				}))?.messageName ?? "",
				chatId: space
			};
		}
	}
};
//#endregion
//#region extensions/googlechat/src/doctor.ts
function asObjectRecord(value) {
	return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}
function isGoogleChatMutableAllowEntry(raw) {
	const text = raw.trim();
	if (!text || text === "*") return false;
	const withoutPrefix = text.replace(/^(googlechat|google-chat|gchat):/i, "").trim();
	if (!withoutPrefix) return false;
	return withoutPrefix.replace(/^users\//i, "").includes("@");
}
const collectGoogleChatMutableAllowlistWarnings = createDangerousNameMatchingMutableAllowlistWarningCollector({
	channel: "googlechat",
	detector: isGoogleChatMutableAllowEntry,
	collectLists: (scope) => {
		const lists = [{
			pathLabel: `${scope.prefix}.groupAllowFrom`,
			list: scope.account.groupAllowFrom
		}];
		const dm = asObjectRecord(scope.account.dm);
		if (dm) lists.push({
			pathLabel: `${scope.prefix}.dm.allowFrom`,
			list: dm.allowFrom
		});
		const groups = asObjectRecord(scope.account.groups);
		if (groups) for (const [groupKey, groupRaw] of Object.entries(groups)) {
			const group = asObjectRecord(groupRaw);
			if (!group) continue;
			lists.push({
				pathLabel: `${scope.prefix}.groups.${groupKey}.users`,
				list: group.users
			});
		}
		return lists;
	}
});
//#endregion
//#region extensions/googlechat/src/gateway.ts
const loadGoogleChatChannelRuntime$1 = createLazyRuntimeNamedExport(() => import("./channel.runtime-DkProO76.js"), "googleChatChannelRuntime");
async function startGoogleChatGatewayAccount(ctx) {
	const account = ctx.account;
	const statusSink = createAccountStatusSink({
		accountId: account.accountId,
		setStatus: ctx.setStatus
	});
	ctx.log?.info?.(`[${account.accountId}] starting Google Chat webhook`);
	const { resolveGoogleChatWebhookPath, startGoogleChatMonitor } = await loadGoogleChatChannelRuntime$1();
	statusSink({
		running: true,
		lastStartAt: Date.now(),
		webhookPath: resolveGoogleChatWebhookPath({ account }),
		audienceType: account.config.audienceType,
		audience: account.config.audience
	});
	await runPassiveAccountLifecycle({
		abortSignal: ctx.abortSignal,
		start: async () => await startGoogleChatMonitor({
			account,
			config: ctx.cfg,
			runtime: ctx.runtime,
			abortSignal: ctx.abortSignal,
			webhookPath: account.config.webhookPath,
			webhookUrl: account.config.webhookUrl,
			statusSink
		}),
		stop: async (unregister) => {
			unregister?.();
		},
		onStop: async () => {
			statusSink({
				running: false,
				lastStopAt: Date.now()
			});
		}
	});
}
const googlechatSetupAdapter = createPatchedAccountSetupAdapter({
	channelKey: "googlechat",
	validateInput: createSetupInputPresenceValidator({
		defaultAccountOnlyEnvError: "GOOGLE_CHAT_SERVICE_ACCOUNT env vars can only be used for the default account.",
		whenNotUseEnv: [{
			someOf: ["token", "tokenFile"],
			message: "Google Chat requires --token (service account JSON) or --token-file."
		}]
	}),
	buildPatch: (input) => {
		const patch = input.useEnv ? {} : input.tokenFile ? { serviceAccountFile: input.tokenFile } : input.token ? { serviceAccount: input.token } : {};
		const audienceType = input.audienceType?.trim();
		const audience = input.audience?.trim();
		const webhookPath = input.webhookPath?.trim();
		const webhookUrl = input.webhookUrl?.trim();
		return {
			...patch,
			...audienceType ? { audienceType } : {},
			...audience ? { audience } : {},
			...webhookPath ? { webhookPath } : {},
			...webhookUrl ? { webhookUrl } : {}
		};
	}
});
//#endregion
//#region extensions/googlechat/src/setup-surface.ts
const channel = "googlechat";
const ENV_SERVICE_ACCOUNT = "GOOGLE_CHAT_SERVICE_ACCOUNT";
const ENV_SERVICE_ACCOUNT_FILE = "GOOGLE_CHAT_SERVICE_ACCOUNT_FILE";
const USE_ENV_FLAG = "__googlechatUseEnv";
const AUTH_METHOD_FLAG = "__googlechatAuthMethod";
function normalizeOptionalString(value) {
	if (typeof value !== "string") return;
	const trimmed = value.trim();
	return trimmed ? trimmed : void 0;
}
function normalizeStringifiedOptionalString(value) {
	if (typeof value === "string") return normalizeOptionalString(value);
	if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") return normalizeOptionalString(String(value));
}
const googlechatDmPolicy = {
	label: "Google Chat",
	channel,
	policyKey: "channels.googlechat.dm.policy",
	allowFromKey: "channels.googlechat.dm.allowFrom",
	resolveConfigKeys: (cfg, accountId) => (accountId ?? resolveDefaultGoogleChatAccountId(cfg)) !== "default" ? {
		policyKey: `channels.googlechat.accounts.${accountId ?? resolveDefaultGoogleChatAccountId(cfg)}.dm.policy`,
		allowFromKey: `channels.googlechat.accounts.${accountId ?? resolveDefaultGoogleChatAccountId(cfg)}.dm.allowFrom`
	} : {
		policyKey: "channels.googlechat.dm.policy",
		allowFromKey: "channels.googlechat.dm.allowFrom"
	},
	getCurrent: (cfg, accountId) => resolveGoogleChatAccount({
		cfg,
		accountId: accountId ?? resolveDefaultGoogleChatAccountId(cfg)
	}).config.dm?.policy ?? "pairing",
	setPolicy: (cfg, policy, accountId) => {
		const resolvedAccountId = accountId ?? resolveDefaultGoogleChatAccountId(cfg);
		const currentDm = resolveGoogleChatAccount({
			cfg,
			accountId: resolvedAccountId
		}).config.dm;
		return applySetupAccountConfigPatch({
			cfg,
			channelKey: channel,
			accountId: resolvedAccountId,
			patch: { dm: {
				...currentDm,
				policy,
				...policy === "open" ? { allowFrom: addWildcardAllowFrom(currentDm?.allowFrom) } : {}
			} }
		});
	},
	promptAllowFrom: createPromptParsedAllowFromForAccount({
		defaultAccountId: resolveDefaultGoogleChatAccountId,
		message: "Google Chat allowFrom (users/<id> or raw email; avoid users/<email>)",
		placeholder: "users/123456789, name@example.com",
		parseEntries: (raw) => ({ entries: mergeAllowFromEntries(void 0, splitSetupEntries(raw)) }),
		getExistingAllowFrom: ({ cfg, accountId }) => resolveGoogleChatAccount({
			cfg,
			accountId
		}).config.dm?.allowFrom ?? [],
		applyAllowFrom: ({ cfg, accountId, allowFrom }) => applySetupAccountConfigPatch({
			cfg,
			channelKey: channel,
			accountId,
			patch: { dm: {
				...resolveGoogleChatAccount({
					cfg,
					accountId
				}).config.dm,
				allowFrom
			} }
		})
	})
};
const googlechatSetupWizard = {
	channel,
	status: createStandardChannelSetupStatus({
		channelLabel: "Google Chat",
		configuredLabel: "configured",
		unconfiguredLabel: "needs service account",
		configuredHint: "configured",
		unconfiguredHint: "needs auth",
		includeStatusLine: true,
		resolveConfigured: ({ cfg, accountId }) => resolveGoogleChatAccount({
			cfg,
			accountId
		}).credentialSource !== "none"
	}),
	introNote: {
		title: "Google Chat setup",
		lines: [
			"Google Chat apps use service-account auth and an HTTPS webhook.",
			"Set the Chat API scopes in your service account and configure the Chat app URL.",
			"Webhook verification requires audience type + audience value.",
			`Docs: ${formatDocsLink("/channels/googlechat", "googlechat")}`
		]
	},
	prepare: async ({ cfg, accountId, credentialValues, prompter }) => {
		if (accountId === "default" && (Boolean(process.env[ENV_SERVICE_ACCOUNT]) || Boolean(process.env[ENV_SERVICE_ACCOUNT_FILE]))) {
			if (await prompter.confirm({
				message: "Use GOOGLE_CHAT_SERVICE_ACCOUNT env vars?",
				initialValue: true
			})) return {
				cfg: applySetupAccountConfigPatch({
					cfg,
					channelKey: channel,
					accountId,
					patch: {}
				}),
				credentialValues: {
					...credentialValues,
					[USE_ENV_FLAG]: "1"
				}
			};
		}
		const method = await prompter.select({
			message: "Google Chat auth method",
			options: [{
				value: "file",
				label: "Service account JSON file"
			}, {
				value: "inline",
				label: "Paste service account JSON"
			}],
			initialValue: "file"
		});
		return { credentialValues: {
			...credentialValues,
			[USE_ENV_FLAG]: "0",
			[AUTH_METHOD_FLAG]: method
		} };
	},
	credentials: [],
	textInputs: [{
		inputKey: "tokenFile",
		message: "Service account JSON path",
		placeholder: "/path/to/service-account.json",
		shouldPrompt: ({ credentialValues }) => credentialValues[USE_ENV_FLAG] !== "1" && credentialValues[AUTH_METHOD_FLAG] === "file",
		validate: ({ value }) => normalizeStringifiedOptionalString(value) ? void 0 : "Required",
		normalizeValue: ({ value }) => normalizeStringifiedOptionalString(value) ?? "",
		applySet: async ({ cfg, accountId, value }) => applySetupAccountConfigPatch({
			cfg,
			channelKey: channel,
			accountId,
			patch: { serviceAccountFile: value }
		})
	}, {
		inputKey: "token",
		message: "Service account JSON (single line)",
		placeholder: "{\"type\":\"service_account\", ... }",
		shouldPrompt: ({ credentialValues }) => credentialValues[USE_ENV_FLAG] !== "1" && credentialValues[AUTH_METHOD_FLAG] === "inline",
		validate: ({ value }) => normalizeStringifiedOptionalString(value) ? void 0 : "Required",
		normalizeValue: ({ value }) => normalizeStringifiedOptionalString(value) ?? "",
		applySet: async ({ cfg, accountId, value }) => applySetupAccountConfigPatch({
			cfg,
			channelKey: channel,
			accountId,
			patch: { serviceAccount: value }
		})
	}],
	finalize: async ({ cfg, accountId, prompter }) => {
		const account = resolveGoogleChatAccount({
			cfg,
			accountId
		});
		const audienceType = await prompter.select({
			message: "Webhook audience type",
			options: [{
				value: "app-url",
				label: "App URL (recommended)"
			}, {
				value: "project-number",
				label: "Project number"
			}],
			initialValue: account.config.audienceType === "project-number" ? "project-number" : "app-url"
		});
		return { cfg: migrateBaseNameToDefaultAccount({
			cfg: applySetupAccountConfigPatch({
				cfg,
				channelKey: channel,
				accountId,
				patch: {
					audienceType,
					audience: normalizeOptionalString(await prompter.text({
						message: audienceType === "project-number" ? "Project number" : "App URL",
						placeholder: audienceType === "project-number" ? "1234567890" : "https://your.host/googlechat",
						initialValue: account.config.audience || void 0,
						validate: (value) => normalizeStringifiedOptionalString(value) ? void 0 : "Required"
					})) ?? ""
				}
			}),
			channelKey: channel
		}) };
	},
	dmPolicy: googlechatDmPolicy
};
//#endregion
//#region extensions/googlechat/src/channel.ts
const loadGoogleChatChannelRuntime = createLazyRuntimeNamedExport(() => import("./channel.runtime-DkProO76.js"), "googleChatChannelRuntime");
const meta = {
	id: "googlechat",
	label: "Google Chat",
	selectionLabel: "Google Chat (Chat API)",
	docsPath: "/channels/googlechat",
	docsLabel: "googlechat",
	blurb: "Google Workspace Chat app with HTTP webhook.",
	aliases: ["gchat", "google-chat"],
	order: 55,
	detailLabel: "Google Chat",
	systemImage: "message.badge",
	markdownCapable: true
};
const googleChatConfigAdapter = createScopedChannelConfigAdapter({
	sectionKey: "googlechat",
	listAccountIds: listGoogleChatAccountIds,
	resolveAccount: adaptScopedAccountAccessor(resolveGoogleChatAccount),
	defaultAccountId: resolveDefaultGoogleChatAccountId,
	clearBaseFields: [
		"serviceAccount",
		"serviceAccountFile",
		"audienceType",
		"audience",
		"webhookPath",
		"webhookUrl",
		"botUser",
		"name"
	],
	resolveAllowFrom: (account) => account.config.dm?.allowFrom,
	formatAllowFrom: (allowFrom) => formatNormalizedAllowFromEntries({
		allowFrom,
		normalizeEntry: formatAllowFromEntry
	}),
	resolveDefaultTo: (account) => account.config.defaultTo
});
const googlechatActions = {
	describeMessageTool: (ctx) => googlechatMessageActions.describeMessageTool?.(ctx) ?? null,
	extractToolSend: (ctx) => googlechatMessageActions.extractToolSend?.(ctx) ?? null,
	handleAction: async (ctx) => {
		if (!googlechatMessageActions.handleAction) throw new Error("Google Chat actions are not available.");
		return await googlechatMessageActions.handleAction(ctx);
	}
};
const googlechatPlugin = createChatChannelPlugin({
	base: {
		id: "googlechat",
		meta: { ...meta },
		setup: googlechatSetupAdapter,
		setupWizard: googlechatSetupWizard,
		capabilities: {
			chatTypes: [
				"direct",
				"group",
				"thread"
			],
			reactions: true,
			threads: true,
			media: true,
			nativeCommands: false,
			blockStreaming: true
		},
		streaming: { blockStreamingCoalesceDefaults: {
			minChars: 1500,
			idleMs: 1e3
		} },
		reload: { configPrefixes: ["channels.googlechat"] },
		configSchema: buildChannelConfigSchema(GoogleChatConfigSchema),
		config: {
			...googleChatConfigAdapter,
			isConfigured: (account) => account.credentialSource !== "none",
			describeAccount: (account) => describeAccountSnapshot({
				account,
				configured: account.credentialSource !== "none",
				extra: { credentialSource: account.credentialSource }
			})
		},
		approvalCapability: googleChatApprovalAuth,
		secrets: {
			secretTargetRegistryEntries,
			collectRuntimeConfigAssignments
		},
		groups: googlechatGroupsAdapter,
		messaging: {
			normalizeTarget: normalizeGoogleChatTarget,
			targetResolver: {
				looksLikeId: (raw, normalized) => {
					const value = normalized ?? raw.trim();
					return isGoogleChatSpaceTarget(value) || isGoogleChatUserTarget(value);
				},
				hint: "<spaces/{space}|users/{user}>"
			}
		},
		directory: googlechatDirectoryAdapter,
		resolver: { resolveTargets: async ({ inputs, kind }) => {
			return inputs.map((input) => {
				const normalized = normalizeGoogleChatTarget(input);
				if (!normalized) return {
					input,
					resolved: false,
					note: "empty target"
				};
				if (kind === "user" && isGoogleChatUserTarget(normalized)) return {
					input,
					resolved: true,
					id: normalized
				};
				if (kind === "group" && isGoogleChatSpaceTarget(normalized)) return {
					input,
					resolved: true,
					id: normalized
				};
				return {
					input,
					resolved: false,
					note: "use spaces/{space} or users/{user}"
				};
			});
		} },
		actions: googlechatActions,
		doctor: {
			dmAllowFromMode: "nestedOnly",
			groupModel: "route",
			groupAllowFromFallbackToAllowFrom: false,
			warnOnEmptyGroupSenderAllowlist: false,
			collectMutableAllowlistWarnings: collectGoogleChatMutableAllowlistWarnings
		},
		status: createComputedAccountStatusAdapter({
			defaultRuntime: createDefaultChannelRuntimeState(DEFAULT_ACCOUNT_ID),
			collectStatusIssues: (accounts) => accounts.flatMap((entry) => {
				const accountId = entry.accountId ?? "default";
				const enabled = entry.enabled !== false;
				const configured = entry.configured === true;
				if (!enabled || !configured) return [];
				const issues = [];
				if (!entry.audience) issues.push({
					channel: "googlechat",
					accountId,
					kind: "config",
					message: "Google Chat audience is missing (set channels.googlechat.audience).",
					fix: "Set channels.googlechat.audienceType and channels.googlechat.audience."
				});
				if (!entry.audienceType) issues.push({
					channel: "googlechat",
					accountId,
					kind: "config",
					message: "Google Chat audienceType is missing (app-url or project-number).",
					fix: "Set channels.googlechat.audienceType and channels.googlechat.audience."
				});
				return issues;
			}),
			buildChannelSummary: ({ snapshot }) => buildPassiveProbedChannelStatusSummary(snapshot, {
				credentialSource: snapshot.credentialSource ?? "none",
				audienceType: snapshot.audienceType ?? null,
				audience: snapshot.audience ?? null,
				webhookPath: snapshot.webhookPath ?? null,
				webhookUrl: snapshot.webhookUrl ?? null
			}),
			probeAccount: async ({ account }) => (await loadGoogleChatChannelRuntime()).probeGoogleChat(account),
			resolveAccountSnapshot: ({ account }) => ({
				accountId: account.accountId,
				name: account.name,
				enabled: account.enabled,
				configured: account.credentialSource !== "none",
				extra: {
					credentialSource: account.credentialSource,
					audienceType: account.config.audienceType,
					audience: account.config.audience,
					webhookPath: account.config.webhookPath,
					webhookUrl: account.config.webhookUrl,
					dmPolicy: account.config.dm?.policy ?? "pairing"
				}
			})
		}),
		gateway: { startAccount: startGoogleChatGatewayAccount }
	},
	pairing: { text: googlechatPairingTextAdapter },
	security: googlechatSecurityAdapter,
	threading: googlechatThreadingAdapter,
	outbound: googlechatOutboundAdapter
});
//#endregion
export { googlechatSetupWizard as n, googlechatSetupAdapter as r, googlechatPlugin as t };
