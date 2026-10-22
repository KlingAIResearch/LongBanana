# Architecture

LongBanana separates dataset loading, execution, model transport, image generation,
and scoring. A supervisor controls each experiment while agents run in isolated
Bubblewrap environments. Generation and evaluation have independent configurations.

## Dataset contracts

`open_v1` and `open_v1p5` each contain 90 cases and 32 reference images per case.
`open_v1` additionally supplies one public background per case, placed before the
reference images in generation inputs. `open_v1p5` supplies no additional background.

| View | Contents | Runtime access |
| --- | --- | --- |
| Public | Instruction, references, optional public background | Generation agent for the selected case |
| Evaluation | Check text, guidance, options, reference bindings | Supervisor; each judge receives one check |
| Research | Graphs, simulated targets, construction and quality metadata | Separate artifacts, not mounted into agents |

Dataset identity includes the release and revision, not only the case ID.
References retain their order, filenames, and image bytes. Released assets have
checksums. Downloadable research materials are not a secret test set; this
separation controls what each running agent can access.

The evaluation contracts contain 4,670 and 5,170 checks respectively. Compilation
is deterministic: direct reference bindings are preserved; node-based requirements
resolve references through graph evidence edges, including references bound
directly to the source relationship or constraint. Missing bindings are errors,
not an invitation to select references using a language model. A check without
explicit reference IDs is not automatically classified as a global check.

## Execution architecture

```text
Configuration + dataset manifest
              |
          Supervisor
              |
              +-- Generation: one sandbox per case
              |     Agent -> planning proxy -> selected LLM
              |     MCP   -> image proxy    -> Gemini 3.1 Flash Image
              |     Final image + execution trace
              |
              +-- Evaluation: generated image + bound checklist
                    One sandbox per check, or a direct VLM request
                    Judgment + evidence + score + usage
```

The supervisor owns credentials, validates inputs, schedules tasks, and persists
results. Each sandbox has an isolated HOME, writable workspace and output directory,
and read-only inputs and dependencies. Generation agents do not receive graphs,
checklists, simulated targets, or existing scores. Judges receive the candidate
and references bound to their check, without human labels.

Bubblewrap provides filesystem, process, and IPC isolation. Networking is shared;
this is not a network-domain allowlist. Model and image requests use authenticated
loopback services. Upstream credentials remain in the supervisor. Isolation checks
must pass before execution; there is no unsandboxed fallback.

Isolated procfs and minimal proc mode support different Linux container constraints.
Agent, MCP, Gateway, and descendant processes are cleaned up when their owning task
exits or times out. Local execution is the portable default; cluster submission
belongs in an optional executor adapter.

## Agent adapters

| Agent | Generation | Evaluation |
| --- | --- | --- |
| Codex | Shared native prompt; native image viewing; Gemini MCP | Native image viewing and check-level answer parsing |
| Claude Code | Shared native prompt; native Read; Gemini MCP | Native Read and check-level answer parsing |
| OpenClaw | Strategy-based generation and MCP image viewing | Static Judge, with optional visual specialist agents |

Behavior profiles version prompts, tools, strategy, image handling, reasoning,
parsing, timeouts, and retries. They preserve each agent's workflow; a common
configuration interface does not imply identical prompts. Backend guidance is
available for optional reading. Agents control generation and editing counts
within the configured execution timeout.

Native judges must actually inspect the candidate. All bound references are
provided, but opening every reference is not required. OpenClaw retains its own
image attachment and specialist workflow. Specialist mode waits for completed,
nonempty evidence before the main judge's final decision. Concurrent checks use
separate session state and, where required, separate Gateways.

## Model transport

Model family, provider, exact model ID, endpoint, and protocol are explicit fields.
Generation and evaluation can use different models. Public configurations target
the official Google, OpenAI, and Anthropic APIs; users may supply compatible endpoints.

Codex prefers Responses, Claude Code prefers Messages, and OpenClaw uses its
supported provider interface. Conversion is used only when explicitly configured.
Same-protocol forwarding preserves tool calls, signatures, opaque reasoning,
encrypted content, and streaming events. Conversion is tested separately.
Requests do not silently switch model, provider, or protocol after errors.

Auxiliary model choices are recorded. Credentials are referenced by environment
variable name rather than embedded in configuration or results. Proxy routing uses
standard user-supplied proxy and bypass settings rather than predefined domains.

## Image generation

The image model is `gemini-3.1-flash-image`. The supervisor selects the endpoint;
agents see one image backend. Native agents receive `generate_image` with `prompt`,
`reference_images`, and optional `output_dir`. OpenClaw retains its reference-viewing
tool. The schema adds neither model selection nor a numeric reference cap.

Image processing is versioned separately for each path:

- References sent to the image API are resized without enlargement, preserving
  aspect ratio, normally to a long side of at most 1024 pixels. Opaque images use
  JPEG quality 90; alpha images preserve PNG.
- Generated originals are saved at full resolution. Tool responses provide
  aspect-preserving previews of at most 1024 pixels.
- Planning-model image transport follows the selected profile. Optional JPEG
  quality 90 encoding preserves dimensions and only replaces smaller payloads.
  Text, tool schemas, and reasoning items remain unchanged.

Dataset files are not modified. A changed image policy defines a new experiment
configuration rather than silently changing a resumed run.

## Results and scoring

An experiment records dataset revision, model deployment, runtime versions,
prompt and tool hashes, image policy, reasoning, and retry parameters. Each task
preserves attempts, traces, final results, and usage. Summaries are rebuildable.

Resume reuses valid results only when fingerprints and output hashes match.
Failures retain their history. Task locks and stable shards support concurrent
execution; shared-storage runs require working filesystem lock semantics.
Final-image selection follows the chosen agent's completion contract.

Fail, Uncertain, and Pass map to 0, 1, and 2; invalid judgments have no score.
A case score is `100 × mean(check scores) / 2`. Category and overall scores average
case scores. Incomplete runs show coverage and provisional statistics, not a
completed benchmark score. Missing-value overrides require an explicit policy.
Difficulty-weighted reports identify the weight file and evaluation cohort.

Workers, planning requests, image requests, and Gateways have separate concurrency
settings. Infrastructure timeouts do not add an agent-turn or generation-count cap.

## Distribution

Source, datasets, and agent runtimes are separate artifacts. The source package
contains portable examples, dependencies, validation tools, and third-party notices.
Runtime downloads have recorded checksums; existing user environments can be reused.

The package must operate independently of the development checkout. Export paths
are relative to their artifact root. Release archives use explicit file allowlists
and are scanned before publication.
