import { i as postJsonRequest, s as resolveProviderHttpRequestConfig, t as assertOkOrThrowHttpError } from "./shared-BvHHokYC.js";
import { t as isProviderApiKeyConfigured } from "./provider-auth-txAsLrEZ.js";
import "./provider-http-CAeFRFu0.js";
import { n as resolveApiKeyForProvider } from "./provider-auth-runtime-BcC-Tpqi.js";
//#region extensions/image-generation-internal/image-generation-provider.ts
const BASE_URL = "https://example.invalid";
const MODEL_A = "image_generation_a";
const MODEL_A_ENDPOINT = "replace-with-image-model-a";
const MODEL_B = "image_generation_b";
const MODEL_B_ENDPOINT = "replace-with-image-model-b";
const DEFAULT_MODEL = MODEL_A;
const DEFAULT_OUTPUT_MIME = "image/png";
const DEFAULT_SIZE = "1024x1024";
const SUPPORTED_SIZES = [
	"1024x1024",
	"1024x1536",
	"1536x1024"
];
function isModelB(model) {
	return model === MODEL_B;
}
async function generateWithModelA(params) {
	const { response, release } = await postJsonRequest({
		url: `${params.baseUrl}/api/gateway/v1/images/generations`,
		headers: params.headers,
		body: {
			model: MODEL_A_ENDPOINT,
			prompt: params.prompt,
			size: params.size,
			n: params.count,
			quality: "high"
		},
		timeoutMs: params.timeoutMs,
		fetchFn: fetch,
		allowPrivateNetwork: params.allowPrivateNetwork,
		dispatcherPolicy: params.dispatcherPolicy
	});
	try {
		await assertOkOrThrowHttpError(response, "Image generation (model A) failed");
		const images = ((await response.json()).data?.content ?? []).map((entry, index) => {
			if (!entry.b64_json) return null;
			return {
				buffer: Buffer.from(entry.b64_json, "base64"),
				mimeType: DEFAULT_OUTPUT_MIME,
				fileName: `image-${index + 1}.png`
			};
		}).filter((entry) => entry !== null);
		if (images.length === 0) throw new Error("Image generation (model A) returned no images");
		return {
			images,
			model: params.model
		};
	} finally {
		await release();
	}
}
async function generateWithModelB(params) {
	const { response, release } = await postJsonRequest({
		url: `${params.baseUrl}/api/gateway/gemini/v1beta/models/${MODEL_B_ENDPOINT}:generateContent`,
		headers: params.headers,
		body: {
			contents: [{ parts: [{ text: params.prompt }] }],
			generationConfig: { responseModalities: ["TEXT", "IMAGE"] }
		},
		timeoutMs: params.timeoutMs,
		fetchFn: fetch,
		allowPrivateNetwork: params.allowPrivateNetwork,
		dispatcherPolicy: params.dispatcherPolicy
	});
	try {
		await assertOkOrThrowHttpError(response, "Image generation (model B) failed");
		const payload = await response.json();
		let imageIndex = 0;
		const images = (payload.candidates ?? []).flatMap((c) => c.content?.parts ?? []).map((part) => {
			const data = part.inlineData?.data?.trim();
			if (!data) return null;
			const mimeType = part.inlineData?.mimeType ?? DEFAULT_OUTPUT_MIME;
			const ext = mimeType.includes("jpeg") ? "jpg" : mimeType.split("/")[1] ?? "png";
			imageIndex += 1;
			return {
				buffer: Buffer.from(data, "base64"),
				mimeType,
				fileName: `image-${imageIndex}.${ext}`
			};
		}).filter((entry) => entry !== null);
		if (images.length === 0) throw new Error("Image generation (model B) returned no images");
		return {
			images,
			model: params.model
		};
	} finally {
		await release();
	}
}
function buildImageGenerationProvider() {
	return {
		id: "image_generation",
		label: "Image Generation",
		defaultModel: DEFAULT_MODEL,
		models: [MODEL_A, MODEL_B],
		isConfigured: ({ agentDir }) => isProviderApiKeyConfigured({
			provider: "image_generation",
			agentDir
		}),
		capabilities: {
			generate: {
				maxCount: 4,
				supportsSize: true,
				supportsAspectRatio: false,
				supportsResolution: false
			},
			edit: {
				enabled: false,
				maxCount: 1,
				maxInputImages: 0,
				supportsSize: false,
				supportsAspectRatio: false,
				supportsResolution: false
			},
			geometry: { sizes: [...SUPPORTED_SIZES] }
		},
		async generateImage(req) {
			const auth = await resolveApiKeyForProvider({
				provider: "image_generation",
				cfg: req.cfg,
				agentDir: req.agentDir,
				store: req.authStore
			});
			if (!auth.apiKey) throw new Error("Image Generation API key missing");
			if ((req.inputImages?.length ?? 0) > 0) throw new Error("Image generation does not support editing");
			const { baseUrl, allowPrivateNetwork, headers, dispatcherPolicy } = resolveProviderHttpRequestConfig({
				baseUrl: void 0,
				defaultBaseUrl: BASE_URL,
				allowPrivateNetwork: false,
				defaultHeaders: {
					Authorization: `Bearer ${auth.apiKey}`,
					"Content-Type": "application/json"
				},
				provider: "image_generation",
				capability: "image",
				transport: "http"
			});
			const model = req.model?.trim() || DEFAULT_MODEL;
			const count = req.count ?? 1;
			const size = req.size ?? DEFAULT_SIZE;
			if (isModelB(model)) return generateWithModelB({
				baseUrl,
				headers,
				allowPrivateNetwork,
				dispatcherPolicy,
				prompt: req.prompt,
				model,
				timeoutMs: req.timeoutMs
			});
			return generateWithModelA({
				baseUrl,
				headers,
				allowPrivateNetwork,
				dispatcherPolicy,
				prompt: req.prompt,
				model,
				count,
				size,
				timeoutMs: req.timeoutMs
			});
		}
	};
}
//#endregion
export { buildImageGenerationProvider as t };
