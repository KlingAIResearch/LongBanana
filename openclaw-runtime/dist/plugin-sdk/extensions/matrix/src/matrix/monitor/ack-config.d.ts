import type { OpenClawConfig } from "openclaw/plugin-sdk/config-runtime";
type MatrixAckReactionScope = "group-mentions" | "group-all" | "direct" | "all" | "none" | "off";
export declare function resolveMatrixAckReactionConfig(params: {
    cfg: OpenClawConfig;
    agentId: string;
    accountId?: string | null;
}): {
    ackReaction: string;
    ackReactionScope: MatrixAckReactionScope;
};
export {};
