# Running experiments

The unified entrypoint implements Codex, Claude Code, and OpenClaw generation and
static agentic judging, plus a direct Gemini VLM baseline. Offline tests and
sandbox fixture tests are distinct from live-provider validation.

## Reuse an environment

Use Python 3.11 or later with Requests and Pillow, an existing Node runtime, and
the pinned agent CLI binaries. No command automatically installs or updates an
environment. From a source checkout:

```bash
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
python -m longbanana --help
python -m unittest discover -s tests -v
```

Bubblewrap must work on the execution host. Every run probes isolation before
starting services; failure never falls back to unsandboxed execution. An existing
MCP `node_modules` directory may be reused. For a fresh deployment, the dependency
lock is in `mcp/image_gen/package-lock.json`; Node must support its dependencies.

## Runtime manifest

Create a local JSON manifest. Command entries are actual file paths, absolute or
relative to that manifest. Versions should describe the supplied binaries.

```json
{
  "codex": {"version": "YOUR_PINNED_VERSION", "command": ["/opt/codex/codex"]},
  "claude-code": {"version": "YOUR_PINNED_VERSION", "command": ["/opt/node/bin/node", "/opt/claude/cli.js"]},
  "node": {"version": "YOUR_PINNED_VERSION", "command": ["/opt/node/bin/node"]}
}
```

The current Claude Code adapter expects the Node-based CLI entrypoint. Native
executable distributions need a separate adapter and are not silently substituted.
Both agents retain their native image-reading tools.

### OpenClaw runtime

`examples/openclaw.json` also requires `OPENCLAW_RUNTIME` (the directory containing
`openclaw.mjs`, `package.json`, and `dist/`), `OPENCLAW_MODULES` (installed Node
dependencies), and `PYTHON_RUNTIME` (an existing Python executable). npm and pnpm
lockfiles are supported. Runtime assets and lockfiles are hashed into experiment
identity. Keep the Python environment separate from the source checkout; it must
remain executable inside the sandbox with its environment prefix mounted read-only.

The retained OpenClaw profile uses `thinking: high`. Generation uses the `pipe`
strategy with `pipe_mode: multi`. Judge accepts `subagents: true` to enable visual
specialists; global checks retain the ordinary Judge branch. Set it to `false`
for ordinary static judging. Each check has independent state and, when needed,
its own Gateway. A shared credential transport does not share Gateway sessions.

Default timeouts preserve the retained profile: 90,000 seconds for generation,
900 seconds for judging, and 300 seconds per MCP call. Set `timeout` explicitly
when choosing another execution budget. `invalid_retries` defaults to five.
Do not compare runs with changed budgets or retries as identical configurations.

The OpenClaw runtime must support the retained MCP and visual-specialist profile.
A matching version label alone is insufficient: record the runtime asset hashes
and run the sandbox fixture tests before using another build.

## Configuration

Copy an example and set `DATASET_MANIFEST`, `RUNTIME_MANIFEST`, `BWRAP_PATH`, and
`MCP_MODULES` to your existing files/directories. Set the selected model ID and
provider API key in the environment. Examples use the official provider URLs.
The Gemini model fragment can replace an experiment's `model` object when explicit
protocol conversion is desired. Thinking-block conversion from Anthropic is not
supported; use native Messages for that workflow.

Generation and judging may use different configurations. Judge does not start an
image-generation service. Credentials remain in the supervisor; agents receive
only randomly generated loopback tokens. `headers_env` supports compatible
endpoints without embedding header secrets. Do not commit local configurations.

## Validate, run, and resume

```bash
python -m longbanana validate-data "$DATASET_MANIFEST" --evaluation
python -m longbanana generate --config examples/codex.json --output runs/gen --case LAC-001 --dry-run
python -m longbanana generate --config examples/codex.json --output runs/gen --case LAC-001
python -m longbanana generate --config examples/codex.json --output runs/gen --resume
python -m longbanana judge --config examples/codex.json --candidates runs/gen/candidates.json --output runs/judge
python -m longbanana judge --config examples/codex.json --candidates runs/gen/candidates.json --output runs/judge --resume
python -m longbanana judge-direct --config examples/direct-vlm.json --candidates runs/gen/candidates.json --output runs/direct --resume
```

`--dry-run` validates inputs and runtime file availability without calling an API
or launching an agent. It is not an isolation or live-model test. Repeat `--case`
to select a subset. `--num-shards N --shard-index I` selects stable input positions.
Disjoint shards can share an output directory with `--resume`; task locks prevent
duplicate execution, and summaries are serialized. Shared storage must support
POSIX file locks.

Success records are reused only with matching configuration, input hashes, code,
runtime, and output hashes. Worker count may change; model/image concurrency,
prompt code, reasoning or image policy changes require a new experiment directory.
Each retry preserves the previous attempt. Do not change a candidate manifest
under an existing Judge experiment.

### Direct visual baseline

`judge-direct` needs no agent runtime, Node, MCP, or Gateway. It sends the candidate
followed by the check's bound references directly to Gemini; `global_check`
receives only the candidate. It retains the original round-zero rubric, RGB PNG
encoding with a maximum side of 1024 pixels, 8192 output-token request, and up to
ten attempts for invalid responses. An invalid final result has no numeric score.
Reasoning settings are not added to the original payload. Usage is accumulated
over attempts and provider responses are recorded in each attempt's `api_calls.jsonl`.
Only the transport and the shared experiment storage are new.

## Outputs

- `experiment.json`: experiment identity and fingerprints.
- `attempts/`: execution traces, task-local workspaces, and images.
- `results/`: latest per-task records; invalid results have no score.
- `candidates.json`: accepted generation images and checksums.
- `summary.json`: coverage and case-mean scores; incomplete scores are provisional.

Run directories are local research artifacts, not source-release contents. Review
them before sharing: they contain task images, traces, model IDs, and local paths.

## Offline sandbox smoke

On a Linux execution host with existing runtimes, run:

```bash
python tools/smoke_openclaw.py --config local/openclaw.json --output runs/smoke-judge
python tools/smoke_openclaw.py --config local/openclaw.json --output runs/smoke-gen --phase generate
```

Only runtime paths are taken from the supplied configuration. Synthetic images
and a local deterministic model fixture replace the dataset and providers. Judge
tests cover ordinary checks, visual specialists, and resume; generation exercises
the real MCP process and image transport. These tests do not measure model quality.
Use a new output directory for each invocation.
