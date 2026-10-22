import type { WizardPrompter } from "openclaw/plugin-sdk/matrix-runtime-shared";
import { type ChannelSetupWizardAdapter } from "openclaw/plugin-sdk/setup";
import type { CoreConfig } from "./types.js";
declare function promptMatrixAllowFrom(params: {
    cfg: CoreConfig;
    prompter: WizardPrompter;
    accountId?: string;
}): Promise<CoreConfig>;
export declare const matrixOnboardingAdapter: ChannelSetupWizardAdapter;
export declare const __testing: {
    promptMatrixAllowFrom: typeof promptMatrixAllowFrom;
};
export {};
