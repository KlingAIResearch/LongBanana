# Runtime versions

The retained execution profile used the following runtime versions. They are
compatibility pins, not recommendations to upgrade an existing experiment.

| Component | Version | Distribution |
| --- | --- | --- |
| Codex CLI | 0.158.0 | Obtain separately from the upstream project |
| Claude Code | 2.0.77 | Node-based CLI entrypoint, obtained separately |
| Node.js | 22.14.0 | Obtain separately from Node.js |
| OpenClaw | 2026.4.16, retained build | Pinned source repository snapshot below |

Supply a working Bubblewrap executable and record its version and hash with the
run. No runtime, dependency, or environment is installed automatically. Agent
runtimes and their dependencies remain subject to their upstream terms.

## Retained OpenClaw build

The retained runtime build is in the public repository
`Hooccee/LongBanana_open`, commit
`7f7da383d131f8ef3cc3ad43303d31a9f741fea5`, under `openclaw-runtime/`.
The Git tree ID for that directory is
`7afb36e3e3187795376f17c356af0fdca46b9329`.

Use that complete directory, including its MIT license, rather than substituting
an arbitrary upstream build with the same version string. The retained build
contains the MCP and child-agent behavior used by the existing workflow. These
are built JavaScript assets; this snapshot is not a claim of reproducible
compilation from an unmodified upstream tag.

For example, in a separate runtime checkout:

```bash
git clone https://github.com/Hooccee/LongBanana_open.git runtime-checkout
git -C runtime-checkout checkout --detach 7f7da383d131f8ef3cc3ad43303d31a9f741fea5
git -C runtime-checkout rev-parse HEAD:openclaw-runtime
```

Set `OPENCLAW_RUNTIME` to that checkout's `openclaw-runtime` directory and
`OPENCLAW_MODULES` to a separately provisioned dependency directory. Runtime and
dependency-lock hashes enter experiment identity. Provision compatible dependencies
separately and run the offline sandbox fixtures on your execution host before
starting an experiment. See [running experiments](running.md).
