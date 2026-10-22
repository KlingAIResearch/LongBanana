# Release Packaging

The published project is self-contained and written for users configuring their
own machines and API accounts. The Git checkout includes the pinned OpenClaw
runtime and its checksum manifest. Datasets, Node dependencies, and the other
agent CLIs are distributed separately.

## Publication destinations

GitHub hosts source code, tests, configuration examples, and documentation.
The `main` branch contains the sandboxed implementation and is the default branch.
Preserve existing remote history when publishing updates.
Never force-update an existing remote branch.

Hugging Face hosts the two independent dataset archives, `open_v1.tar.zst` and
`open_v1p5.tar.zst`, their SHA-256 checksums, and the dataset card. Do not place
dataset archives, private migration evidence, or raw experiment outputs in the
code branch.

Preparation is local only. Creating remote branches, uploading artifacts, and
changing repository visibility require a separate publication instruction.

## Project website

The same repository hosts the [Project Page](https://klingairesearch.github.io/LongBanana/)
and [Gallery](https://klingairesearch.github.io/LongBanana/gallery/) on an independent
`gh-pages` branch. The `main` branch remains the default code branch.
In **Settings → Pages**, select **Deploy from a branch**, `gh-pages`, and `/ (root)`.
Keep `.nojekyll` at the website root so GitHub serves the static files directly.

Maintain the website in a separate checkout:

```bash
git clone --branch gh-pages --single-branch https://github.com/KlingAIResearch/LongBanana.git longbanana-site
cd longbanana-site
python -m http.server 8000 --bind 127.0.0.1
```

Use relative asset and navigation URLs so the site works beneath `/LongBanana/`.
The Gallery uses `gallery/visual-data/cases.json` and the corresponding public
preview images. Preserve attribution notices, check links and image availability,
and publish website-only updates to `gh-pages`, not `main`.

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
