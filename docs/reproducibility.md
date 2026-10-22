# Reproducibility and Validation

Behavior profiles identify instructions, tool schemas, guides, parsing rules,
image policies, and execution settings. Changing a profile, dataset revision,
model, provider, or image policy creates a new setting. Worker counts can change
without changing task semantics.

## Validation layers

1. **Data:** check image hashes, instructions, reference ordering, check IDs,
   and bindings independently for each release.
2. **Execution contracts:** compare prompts, schemas, payloads, image transformations,
   and parsed answers against fixed fixtures.
3. **Isolation:** inputs are read-only; host files, credentials, simulated targets,
   and unrelated tasks are unavailable inside each sandbox.
4. **Recovery:** matching completed tasks cause no new requests on resume.
   Invalid results remain distinguishable from scored failures.
5. **Live integrations:** test tool calls, image inspection, generation, and judging.
   Verify specialist completion and final reassessment when subagents are enabled.

Record validation separately for each Agent, model protocol, workflow, and subagent
mode. Implementation or connectivity alone does not establish successful multi-step
execution.

## Repeatability

Deterministic validation establishes matching inputs and execution behavior.
Generative APIs can produce different images and judgments across repeated runs.
Statistical equivalence requires paired repeated experiments and predefined criteria.

Record the exact model ID, provider, runtime version, profile hashes, checksums,
timeouts, and reasoning settings. Same-named models from different providers are
different deployments until demonstrated otherwise.

Check scores are Fail=0, Uncertain=1, Pass=2; invalid judgments are null. Completed
scores require valid results for all planned checks unless the report states a
missing-value policy. Weighted metrics identify their weights and reference cohort.
Unavailable token usage is marked explicitly; placeholder zeros are not measured
zero usage. Setup, execution, and total time are separate;
skipped tasks do not contribute new inference time.

## Reproducible checks

Run the offline suite from the source checkout:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite covers dataset hashes and bindings, release-scoped task IDs, credential
isolation, experiment identity, resume, case-mean scoring, and protocol transport.
Local deterministic fixtures test transport behavior without provider credentials.
Passing these checks does not establish live-provider compatibility, image
quality, or statistical score equivalence. Test your configured integration on
your execution host before starting an experiment.

Dataset checksum and schema validation establish integrity, not visual quality,
privacy clearance, or redistribution rights. See the dataset card for limitations.
