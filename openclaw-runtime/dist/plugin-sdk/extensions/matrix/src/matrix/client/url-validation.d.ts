import { type LookupFn } from "openclaw/plugin-sdk/ssrf-runtime";
export declare function validateMatrixHomeserverUrl(homeserver: string, opts?: {
    allowPrivateNetwork?: boolean;
}): string;
export declare function resolveValidatedMatrixHomeserverUrl(homeserver: string, opts?: {
    dangerouslyAllowPrivateNetwork?: boolean;
    allowPrivateNetwork?: boolean;
    lookupFn?: LookupFn;
}): Promise<string>;
