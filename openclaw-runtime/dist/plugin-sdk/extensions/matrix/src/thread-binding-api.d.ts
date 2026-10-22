export declare const defaultTopLevelPlacement: "child";
export declare function resolveMatrixInboundConversation(params: {
    to?: string;
    conversationId?: string;
    threadId?: string | number;
}): {
    parentConversationId?: string | undefined;
    conversationId: string;
} | null;
