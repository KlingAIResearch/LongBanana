import { n as describeImagesWithModel, t as describeImageWithModel } from "./image-runtime-CkGyuGok.js";
import "./media-understanding-DIrxgiMn.js";
//#region extensions/zai/media-understanding-provider.ts
const zaiMediaUnderstandingProvider = {
	id: "zai",
	capabilities: ["image"],
	defaultModels: { image: "glm-4.6v" },
	autoPriority: { image: 60 },
	describeImage: describeImageWithModel,
	describeImages: describeImagesWithModel
};
//#endregion
export { zaiMediaUnderstandingProvider as t };
