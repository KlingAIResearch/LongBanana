# Release Packaging

The published project is self-contained and written for users configuring their
own machines and API accounts. Source, datasets, and runtimes are separate artifacts.

## Publication destinations

GitHub hosts source code, tests, configuration examples, and documentation.
The `main` branch contains the sandboxed implementation and is the default branch.
Preserve existing remote history when publishing updates.
Never force-update an existing remote branch.

Hugging Face hosts the two independent dataset archives, `open_v1.tar.zst` and
`open_v1p5.tar.zst`, their SHA-256 checksums, and the dataset card. Do not place
dataset images, private migration evidence, or experiment outputs in Git history.

Preparation is local only. Creating remote branches, uploading artifacts, and
changing repository visibility require a separate publication instruction.

## Public configuration

Examples use official API endpoints and environment-variable references for
credentials. Custom URLs and authentication headers are user configuration, with
no organization-specific defaults. Dataset names are `open_v1` and `open_v1p5`;
research provenance uses public identifiers and asset hashes.

Migration records, local path mappings, credentials, operational logs, deployment
inventories, and test-account configurations stay outside the release tree.
An ignore rule is not a substitute for removing these files from the artifact.

## Artifact checks

Verify both the release tree and the exact final archive. Check filenames and
contents, including documentation, configuration, metadata, source maps, notebook
outputs, and embedded assets. Exclude caches, environments, personal paths, job
identifiers, private hosts, credentials, and raw traces from source distributions.

Run `python tools/audit_release.py --root .` for the portable source-tree check.
Optional `--policy /path/to/release-policy.json` supplies deployment-specific
forbidden strings from a file outside the release tree. Findings contain locations
and rule names, never matched secret values.

Archive members and binary metadata need their own inspection. Unknown binaries
and symlinks are rejected by the source-tree checker. A text scan alone cannot
certify arbitrary data archives. Record final checksums and validation scope.

## Licenses and reproducibility

Retain copyright notices and public upstream attribution. Deployment cleanup must
not remove legally required attribution. Users obtain agent runtimes according to
their upstream distribution terms.

State which integrations passed, which remain untested, and known data-quality
limitations. Cleanup must not rewrite benchmark requirements, silently change
scoring, or hide failed tests.

Keep private validation receipts and operational test records outside both
publication trees. Public test code should contain synthetic fixtures and
instructions, not credentials, deployment inventories, logs, or execution records.
