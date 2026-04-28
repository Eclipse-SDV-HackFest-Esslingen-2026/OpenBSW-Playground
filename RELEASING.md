# Releasing OpenBSW-Playground

This document describes the release process for **OpenBSW-Playground**, a
hackfest distribution that bundles the Eclipse OpenBSW reference application,
the Eclipse OpenSOVD Classic Diagnostic Adapter, supporting tooling, tests
and documentation.

The pipeline that produces a release is implemented in
[`.github/workflows/release.yml`](.github/workflows/release.yml).

---

## 1. Versioning

Releases use the scheme `vYYYY.MM.MICRO[-suffix]`, e.g.
`v2026.04.0-hackfest`. The version lives only in the git tag — there is no
version file to bump in source.

`main` always points to the latest published release. `development` is the
permanent integration branch. All work happens on `feature/<name>` branches
and is squash-merged into `development`. Only the `@syspilot.release` agent
may merge `development` into `main` and create release tags.

## 2. Release pipeline (`release.yml`)

Triggers:

- `push` of a tag matching `v*` — produces a public GitHub Release.
- `workflow_dispatch` — dry-run from any branch; produces artifacts but
  does **not** publish a GitHub Release and does **not** push to GHCR.

Jobs:

| Job                | Purpose                                                                 |
| ------------------ | ----------------------------------------------------------------------- |
| `build-posix-sovd` | Build `app.sovdDemo.elf` via the `posix-freertos-sovd` CMake preset.    |
| `build-s32k148`    | Cross-build `app.referenceApp.elf` for S32K148, run `puncover_tool`     |
|                    | for size/stack HTML report and `safety/crcCheck.py` for CRC injection;  |
|                    | export ELF + HEX + reports.                                             |
| `build-cda`        | Build the Real CDA (Rust) Docker image and export the binary.           |
| `build-docs`       | Sphinx HTML build of `doc/` with `-W` (warnings as errors).             |
| `test-gate`        | Tier 1 (unit) + Tier 2 (ECU) tests — release is gated on these.         |
| `package`          | Assemble `OpenBSW-Playground-<tag>.zip` + `SHA256SUMS`.                 |
| `publish-ghcr`     | Tag-push only. Push images to `ghcr.io/<org>/...`. Soft-fails on perm.  |
| `release`          | Tag-push only. Create the GitHub Release and upload the bundle.         |

The release bundle (`OpenBSW-Playground-<tag>.zip`) contains:

- `app.sovdDemo.elf` (POSIX-FreeRTOS SOVD demo binary)
- `app.referenceApp.elf` and `app.referenceApp.hex` for S32K148
- `puncover-report.zip` (size/stack/RAM HTML report)
- `crc-report.txt` (safety CRC injection log)
- `opensovd-cda` (Rust CDA binary)
- `sovd-cda/` (Stub CDA Python sources)
- `grafana/dashboards/` (Grafana dashboards JSON)
- `docs/` (Sphinx HTML site)
- `OpenBSW.mdd` (and any PDX) from `real-sovd-cda/odx-gen/`
- `third_party/` (vendored upstream LICENSE/NOTICE files)
- `SHA256SUMS`

## 3. Cutting a release

1. Land all changes via `feature/<name>` → `development` PRs (squash-merge).
2. Run a `workflow_dispatch` of `release.yml` from `development` and verify
   it goes green end-to-end.
3. `@syspilot.release` opens / squash-merges the `development → main` PR.
   This is the release commit.
4. `@syspilot.release` creates the annotated tag on `main`:

   ```bash
   git checkout main && git pull
   git tag -a v2026.04.0-hackfest -m "Release v2026.04.0-hackfest"
   git push origin v2026.04.0-hackfest
   ```

5. Pushing the tag triggers `release.yml` automatically. Verify:
   - The GitHub Release page shows `OpenBSW-Playground-<tag>.zip` and
     `SHA256SUMS`.
   - GHCR images appear under `ghcr.io/eclipse-sdv-hackfest-esslingen-2026/`
     (or the `publish-ghcr` job logged a permission warning and was skipped
     — this is acceptable per the release policy).
   - All jobs ran green; in particular `test-gate` passed Tier 1 + Tier 2.

The `release` job is idempotent on re-run for the same tag: it reuses the
existing release if present and overwrites the uploaded assets.

## 4. Rollback

Release artifacts live in two places:

- **GitHub Release** — delete via the GitHub UI (or `gh release delete <tag>`).
  Keep the git tag in place if you intend to re-publish under the same
  version after fixing forward.
- **GHCR images** — delete via `https://github.com/orgs/<org>/packages` or
  with `gh api -X DELETE /orgs/<org>/packages/container/<image>/versions/<id>`.

To re-cut a broken release without recycling the tag, fix forward on
`development`, merge to `main`, and tag a new patch version
(`v2026.04.1-hackfest`). Avoid moving an already-pushed tag; the release
pipeline is idempotent for *re-running* the same tag, but moving a tag
changes the source it points to and is considered a release-policy
violation.

## 5. Vendored third-party files

Upstream LICENSE / NOTICE files are vendored under
[`third_party/`](third_party/) and included in every release bundle:

- `third_party/eclipse-openbsw/` — Eclipse OpenBSW
- `third_party/eclipse-opensovd/` — Eclipse OpenSOVD subprojects

When bumping any submodule, refresh the matching files in `third_party/`
and note the new pinned commit in `third_party/eclipse-opensovd/NOTICE`.
