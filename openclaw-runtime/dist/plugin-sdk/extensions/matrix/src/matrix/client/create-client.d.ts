import type { PinnedDispatcherPolicy } from "openclaw/plugin-sdk/ssrf-dispatcher";
import type { SsrFPolicy } from "../../runtime-api.js";
import type { MatrixClient } from "../sdk.js";
export declare function createMatrixClient(params: {
    homeserver: string;
    userId?: string;
    accessToken: string;
    password?: string;
    deviceId?: string;
    persistStorage?: boolean;
    encryption?: boolean;
    localTimeoutMs?: number;
    initialSyncLimit?: number;
    accountId?: string | null;
    autoBootstrapCrypto?: boolean;
    allowPrivateNetwork?: boolean;
    ssrfPolicy?: SsrFPolicy;
    dispatcherPolicy?: PinnedDispatcherPolicy;
}): Promise<MatrixClient>;
