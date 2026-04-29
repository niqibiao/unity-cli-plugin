# AGENTS.md

This file provides guidance to Codex CLI (codex.com) when working with code in this repository.

## Project Overview

Codex CLI plugin providing a thin Python CLI for interacting with Unity Editor/Player via the C# Console HTTP service (`com.zh1zh1.csharpconsole`). Pure stdlib Python — no external dependencies.

## CLI

Entry point: `python "${CODEX_PLUGIN_ROOT}/cli/cs.py" <command> [--json] [args]`

Shared flags: `--project <path>`, `--ip` (default 127.0.0.1), `--port` (default 14500), `--mode editor|runtime`, `--compile-ip` (runtime mode only, default 127.0.0.1), `--compile-port` (runtime mode only, default auto-detect), `--timeout` (default 30), `--json`

### Two-phase lifecycle

- **Pre-setup:** only `setup` and `status` work (pure stdlib, no Unity package needed)
- **Post-setup:** full CLI available after `com.zh1zh1.csharpconsole` is installed and Unity resolves it

### Command-first principle

When a built-in framework command exists, prefer `cs command <ns> <action>` over `cs exec <code>`. Code execution is a fallback, not the default. Use `cs list-commands --json` to discover available commands.

### Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `cs setup [--source URL] [--update]` | pre | Add/update package in Packages/manifest.json |
| `cs status` | pre | Package + connection status + version info |
| `cs exec <code>` | post | Execute C# code |
| `cs command <ns> <action> [args]` | post | Run framework command |
| `cs batch <json-array> [--stop-on-error]` | post | Execute multiple commands in one HTTP roundtrip |
| `cs health` | post | Service health check |
| `cs refresh [--wait TIMEOUT] [--exit-playmode]` | post | Trigger asset refresh + script compilation |
| `cs list-commands` | post | List available commands |
| `cs complete <code> <cursor>` | post | Get completions |
| `cs check-update` | post | Version alignment + update check |
| `cs catalog sync` | post | Sync custom command catalog from live editor |
| `cs catalog list` | post | List cached custom commands (offline) |

## Architecture

```
Codex CLI harness
  ├── Skills (skills/unity-cli-command/, skills/unity-cli-exec-code/)
  ├── Skills (converted from commands): $unity-cli-setup, $unity-cli-status, $unity-cli-refresh, $unity-cli-sync-catalog
  └── CLI (cli/cs.py)
       └── core_bridge.py → dynamically imports csharpconsole_core from Unity package
            └── HTTP POST → Unity Editor/Player service (port 14500 editor / 15500 player)
```

### Dynamic bridge (`cli/core_bridge.py`)

The CLI does **not** bundle `csharpconsole_core`. It locates and imports it at runtime from the installed Unity package to guarantee version consistency. Resolution order:

1. `Packages/manifest.json` `file:` entry (resolves both default and custom local paths)
2. `Library/PackageCache/com.zh1zh1.csharpconsole@*/Editor/ExternalTool~/console-client/`

`ConsoleSession` is a facade that wires up the core modules (`client_base`, `command_protocol`, `config_base`, `output`, `response_parser`, `transport_http`) into one-liner methods: `exec()`, `command()`, `batch()`, `health()`, `complete()`, `list_commands()`, `refresh()`, `emit()`.

Connection errors are automatically retried once (1s delay) to handle transient failures during domain reload.

### Shared constants (`cli/__init__.py`)

`PACKAGE_NAME` and `DEFAULT_SOURCE` are defined once in `cli/__init__.py` and imported by both `cs.py` and `core_bridge.py`.

### Plugin structure

```
.codex-plugin/plugin.json   Plugin manifest
cli/__init__.py              Shared constants (PACKAGE_NAME, DEFAULT_SOURCE)
cli/cs.py                    CLI dispatcher (argparse → pre-setup handlers or ConsoleSession)
cli/core_bridge.py           Dynamic import bridge + ConsoleSession facade
(commands converted to skills)
skills/.../SKILL.md          Skill definition with trigger conditions and usage docs
```

### JSON result envelope

All post-setup commands return: `{ "ok": bool, "exitCode": int, "summary": str, "data": {...} }`

## Command Catalog

Built-in commands (59) are statically documented in `skills/unity-cli-command/SKILL.md`.
User-defined custom commands are cached in `skills/unity-cli-command/dynamic-commands.md` (git-ignored, auto-generated).
Run `$unity-cli-refresh-commands` after registering new C# commands to update the cache.
Run `$unity-cli-sync-catalog` to compare the local catalog with the live command list.

## Development Notes

- **Always ask before pushing** — never `git push` without explicit user confirmation
- No build step, no tests, no external deps — just stdlib Python
- Unity project detection: walks up from cwd looking for an `Assets/` directory
- `find_project_root()` in `cs.py` handles project auto-detection; `--project` flag overrides
- Skills in `skills/` use `$ARGUMENTS` and `${CODEX_PLUGIN_ROOT}` template variables
