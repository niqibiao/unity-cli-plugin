# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When bumping the version, rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`
and start a fresh `## [Unreleased]` block above it. The release workflow extracts
the section matching the pushed tag (without the leading `v`) as release notes.

## [Unreleased]

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
