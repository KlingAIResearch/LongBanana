# Runtime versions

The retained execution profile used the following runtime versions. They are
compatibility pins, not recommendations to upgrade an existing experiment.

| Component | Version | Distribution |
| --- | --- | --- |
| Codex CLI | 0.158.0 | Obtain separately from the upstream project |
| Claude Code | 2.0.77 | Node-based CLI entrypoint, obtained separately |
| Node.js | 22.14.0 | Obtain separately from Node.js |
| OpenClaw | 2026.4.16, retained build | Included in this repository under `openclaw-runtime/` |

Supply a working Bubblewrap executable and record its version and hash with the
run. No runtime, dependency, or environment is installed automatically. Agent
runtimes and their dependencies remain subject to their upstream terms.

## Retained OpenClaw build

The complete retained runtime is included in this repository under
`openclaw-runtime/`. No second repository, private download, or separately built
OpenClaw binary is required. Its original runtime files retain Git tree identity
`7afb36e3e3187795376f17c356af0fdca46b9329`; the added dependency lock and patch are
also covered by `openclaw-runtime.sha256.json`.

Use that complete directory, including its MIT license, rather than substituting
an arbitrary upstream build with the same version string. The retained build
contains the MCP and child-agent behavior used by the existing workflow. These
are built JavaScript assets; this snapshot is not a claim of reproducible
compilation from an unmodified upstream tag.

From the LongBanana source checkout, verify the included files:

```bash
python tools/verify_openclaw_runtime.py
export OPENCLAW_RUNTIME="$PWD/openclaw-runtime"
export OPENCLAW_MODULES="$OPENCLAW_RUNTIME/node_modules"
export PYTHON_RUNTIME="$(command -v python)"
```

### Dependencies

Use Node.js 22.14 or later and pnpm 10.32.1 (the version declared by the bundled
package). If pnpm is available through Corepack, explicitly install the locked
production dependencies with:

```bash
corepack pnpm --dir "$OPENCLAW_RUNTIME" install --prod --frozen-lockfile --ignore-scripts
node "$OPENCLAW_RUNTIME/openclaw.mjs" --version
python tools/verify_openclaw_runtime.py
```

Alternatively, use an already installed pnpm 10.32.1 with the same arguments.
This is a prebuilt runtime, not the full upstream build workspace: do not run
its build, prepare, or postinstall scripts. `--ignore-scripts` intentionally
skips those lifecycle hooks. The retained LongBanana profile does not require
building optional voice/local-model integrations. Dependencies are downloaded
from public package registries; API credentials are not needed for installation.

An existing compatible dependency directory can be reused by setting
`OPENCLAW_MODULES` to its `node_modules` path instead. Nothing is installed by
the harness itself. Dependency locks and runtime asset hashes enter experiment
identity; changing them changes the run identity. The lockfile contains only
the runtime's root importer, not the upstream development workspace.

The bundled runtime is provided in the Git checkout. A Python wheel alone does
not include the runtime; wheel users should point `OPENCLAW_RUNTIME` to this
repository's runtime directory. Node, Python, Bubblewrap, and the selected
provider credentials remain user-supplied. Run the local fixture tests described
in [running experiments](running.md) before launching an experiment.
