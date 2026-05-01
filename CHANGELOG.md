# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When bumping the version, rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`
and start a fresh `## [Unreleased]` block above it. The release workflow extracts
the section matching the pushed tag (without the leading `v`) as release notes.

## [Unreleased]

## [1.4.3] - 2026-04-29

### Changed

- `cs setup` now pins the package to the latest `vMAJOR.MINOR.*` tag in the
  remote that matches the plugin's version, instead of writing a bare URL
  (which Unity resolved to HEAD of the default branch). This eliminates the
  drift that produced `plugin X.Y.x ≠ package X.Z.x` warnings shortly
  after a package release. Discovery uses `git ls-remote --tags`; on no
  match or network failure, setup falls back to HEAD with a one-line
  warning. Pass `--no-pin` to opt out, or `--source URL#tag` to pin
  explicitly.
- `cs setup --method local` now `git checkout`s the resolved tag in the
  local clone (fresh or existing). The clone ends in detached HEAD; if you
  intend to develop in the clone, run `git checkout main` afterward.

### Fixed

- `cs setup` no longer prints a misleading `Pinning to vX.Y.Z` line (and
  no longer hits the network) on no-op runs where the package is already
  installed and `--update` was not passed. Pin resolution is now lazy.
- Release workflow now passes `--title "vX.Y.Z"` to `gh release create` so
  the rendered release title is just the tag, not the GitHub web fallback
  of `{tag}: {commit subject}`.

## [1.4.2] - 2026-04-29

### Added

- `cs exec --file PATH` reads C# code from a file. Useful for long or
  multi-line snippets where shell quoting would otherwise be painful.
  UTF-8 BOM is stripped automatically (handles files saved by Visual
  Studio / Rider / Unity).
- Empty / unreadable files are rejected with a clean parser error
  instead of silently sending empty code to Roslyn.

### Fixed

- Shared flags (`--project`, `--ip`, `--port`, `--mode`, `--timeout`,
  `--json`, …) placed **before** the subcommand are no longer reset to
  their defaults by the subparser. Both `cs --project X status` and
  `cs status --project X` now behave the same.

### Workflow

- Release notes are sourced from this file. The `release.yml` workflow
  looks up the section matching the pushed tag and falls back to
  `--generate-notes` when no matching section is present.
- The Codex companion plugin now publishes its own GitHub Release for
  every `vX.Y.Z-codex` tag, mirroring the main release. Previously the
  `-codex` tag was created but no Release was attached, because tags
  pushed by `GITHUB_TOKEN` cannot trigger other workflows.
