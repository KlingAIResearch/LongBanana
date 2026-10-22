# Dataset artifact format

Each dataset is independent of the source package. Its `manifest.json` identifies
the release, revision, checksums, and expected counts:

```json
{
  "schema_version": 1,
  "release": "open_v1",
  "revision": "1",
  "public_tasks": {"path": "public/tasks.jsonl", "sha256": "SHA256_OF_FILE"},
  "checks": {"path": "evaluation/checks.jsonl", "sha256": "SHA256_OF_FILE"},
  "counts": {"cases": 90, "references": 2880, "backgrounds": 90, "checks": 4670}
}
```

A public task contains `case_id`, `category`, `prompt`, an ordered `references`
array, and optional `background`. References have `id`, relative `path`, and
`sha256`; the background has `path` and `sha256`. Original filenames and bytes
are retained. For generation, the background comes first, then the references
in their declared order. Only these fields are staged for the generation agent.

A check contains `case_id`, `check_id`, `category`, `question`, `guide`, `options`,
`option_desc`, and ordered `reference_ids`. Its reference set is fixed by the
dataset, not selected by the agent. The native Judge may decide which supplied
references it needs to open. Empty bindings require `candidate_only_reason`;
they do not automatically change the check category to `global_check`.

Graph-based compilation follows explicit `reference_ids` or matches check
`members` to `evidence_edges.dst`, including evidence explicitly bound to the
check's source edge or constraint ID, then orders bound references by graph order.
Missing nodes, unknown references, and unexplained empty bindings are errors.
The compiler does not infer new bindings from natural-language descriptions.

## Graph-check projection

`graph-check-projection-1` preserves each source check ID and requirement verbatim.
Source kinds `obligation`, `edge`, and `constraint` become `reference_obligation`,
`graph_relation`, and `graph_constraint`. None selects the legacy `global_check`
execution branch, including checks with an approved candidate-only binding.

For graph checks without historical Judge fields, the guide is empty and the
answer vocabulary is `pass`, `fail`, `uncertain`, scored as 2, 0, and 1. This is
an explicitly versioned projection, not a claim that historical Judge inputs or
scores already existed for this release. The original release's check fields
are imported unchanged and do not use this projection.

Missing bindings require separate review records tied to graph and check digests.
The projection refuses stale records, unknown references, unconsumed decisions,
and overrides of explicit source bindings. Raw review authentication is a dataset
publication step; a model's approval flag alone is not proof. Review metadata is
kept outside the task JSON supplied to the Judge.

Evaluation files contain no expected answers, previous scores, human judgments,
or simulated targets. Graphs and simulated targets belong to separate research
artifacts. The loader verifies all selected assets and rejects paths escaping
the artifact root. A valid checksum is an integrity check, not a content-license
or privacy review.
