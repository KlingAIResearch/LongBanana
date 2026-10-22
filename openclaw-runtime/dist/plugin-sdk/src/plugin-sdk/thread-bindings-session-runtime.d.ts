export { resolveThreadBindingFarewellText } from "../channels/thread-bindings-messages.js";
export { registerSessionBindingAdapter, unregisterSessionBindingAdapter, type BindingTargetKind, type SessionBindingAdapter, type SessionBindingRecord, } from "../infra/outbound/session-binding-service.js";
type ThreadBindingLifecycleRecord = {
    boundAt: number;
    lastActivityAt: number;
    idleTimeoutMs?: number;
    maxAgeMs?: number;
};
export declare function resolveThreadBindingLifecycle(params: {
    record: ThreadBindingLifecycleRecord;
    defaultIdleTimeoutMs: number;
    defaultMaxAgeMs: number;
}): {
    expiresAt?: number;
    reason?: "idle-expired" | "max-age-expired";
};
