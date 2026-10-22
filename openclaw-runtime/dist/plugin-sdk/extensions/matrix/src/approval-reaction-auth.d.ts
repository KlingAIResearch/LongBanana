import type { CoreConfig } from "./types.js";
type MatrixApprovalReactionKind = "exec" | "plugin";
export declare function isMatrixApprovalReactionAuthorizedSender(params: {
    cfg: CoreConfig;
    accountId?: string | null;
    senderId?: string | null;
    approvalKind: MatrixApprovalReactionKind;
}): boolean;
export {};
