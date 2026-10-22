import { fetchWithRuntimeDispatcherOrMockedGlobal, isMockedFetch } from "openclaw/plugin-sdk/runtime-fetch";
import { closeDispatcher, createPinnedDispatcher, resolvePinnedHostnameWithPolicy, type PinnedDispatcherPolicy, type SsrFPolicy } from "openclaw/plugin-sdk/ssrf-dispatcher";
export { closeDispatcher, createPinnedDispatcher, fetchWithRuntimeDispatcherOrMockedGlobal, isMockedFetch, resolvePinnedHostnameWithPolicy, type PinnedDispatcherPolicy, type SsrFPolicy, };
export declare function buildTimeoutAbortSignal(params: {
    timeoutMs?: number;
    signal?: AbortSignal;
}): {
    signal?: AbortSignal;
    cleanup: () => void;
};
