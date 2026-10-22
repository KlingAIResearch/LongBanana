import { r as logVerbose } from "./globals-BXNcbNaX.js";
import { f as resolveDefaultModelForAgent } from "./model-selection-BbGKRLeC.js";
import { t as requireApiKey } from "./model-auth-runtime-shared-B6OTbwnu.js";
import "./tokens-HkZ7pDxX.js";
import "./heartbeat-CrKi0n28.js";
import { r as getApiKeyForModel } from "./model-auth-Dv304Zmk.js";
import "./chunk-Czf-8-kf.js";
import { n as resolveModelAsync } from "./model-BE4x7axZ.js";
import "./dispatch-CFIeto2Y.js";
import "./provider-dispatcher-Dxjj7MKM.js";
import "./get-reply-CG0_g2vt.js";
import "./abort-coUKjsqL.js";
import "./btw-command-BEb6Z0kd.js";
import { t as prepareModelForSimpleCompletion } from "./simple-completion-transport-DYdPFtFM.js";
import { completeSimple } from "@mariozechner/pi-ai";
//#region src/auto-reply/reply/conversation-label-generator.ts
const DEFAULT_MAX_LABEL_LENGTH = 128;
const TIMEOUT_MS = 15e3;
function isTextContentBlock(block) {
	return block.type === "text";
}
async function generateConversationLabel(params) {
	const { userMessage, prompt, cfg, agentId, agentDir } = params;
	const maxLength = typeof params.maxLength === "number" && Number.isFinite(params.maxLength) && params.maxLength > 0 ? Math.floor(params.maxLength) : DEFAULT_MAX_LABEL_LENGTH;
	const modelRef = resolveDefaultModelForAgent({
		cfg,
		agentId
	});
	const resolved = await resolveModelAsync(modelRef.provider, modelRef.model, agentDir, cfg);
	if (!resolved.model) {
		logVerbose(`conversation-label-generator: failed to resolve model ${modelRef.provider}/${modelRef.model}`);
		return null;
	}
	const completionModel = prepareModelForSimpleCompletion({
		model: resolved.model,
		cfg
	});
	const apiKey = requireApiKey(await getApiKeyForModel({
		model: completionModel,
		cfg,
		agentDir
	}), modelRef.provider);
	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
	try {
		const text = (await completeSimple(completionModel, { messages: [{
			role: "user",
			content: `${prompt}\n\n${userMessage}`,
			timestamp: Date.now()
		}] }, {
			apiKey,
			maxTokens: 100,
			temperature: .3,
			signal: controller.signal
		})).content.filter(isTextContentBlock).map((block) => block.text).join("").trim();
		if (!text) return null;
		return text.slice(0, maxLength);
	} finally {
		clearTimeout(timeout);
	}
}
//#endregion
export { generateConversationLabel as t };
