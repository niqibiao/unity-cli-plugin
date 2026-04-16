# Custom Command Enhancement Design

## Overview

Enhance the unity-cli-plugin to make custom command discovery and consumption a first-class workflow. **Only this repo is modified** — the Unity C# package (`com.zh1zh1.csharpconsole` v1.3.1) is unchanged.

## Current State

| Component | State |
|-----------|-------|
| CLI `list-commands` | Passes through Unity response; no filtering |
| Custom command cache | `dynamic-commands.md` — git-ignored Markdown table, created on demand |
| `cs status` | Text-only output; no `--json` structured output |
| `/unity-cli-sync-catalog` | Exists — compares SKILL.md catalog with live command list |
| `/unity-cli-refresh-commands` | Exists — queries live editor, filters builtin namespaces, writes `dynamic-commands.md` |
| Built-in command count | 73 in SKILL.md (CLAUDE.md says 59 — outdated) |
| Plugin version | 1.3.1 |

### What's missing

- No `--type` filtering on `list-commands` (must query all then manually filter)
- No persistent per-project catalog — Markdown cache is fragile and single-project
- `cs status` has no JSON output for agent consumption

## Builtin vs Custom — CLI-side inference

The Unity package does not provide a `commandType` field. The CLI infers it from known builtin namespaces:

```
editor, gameobject, component, transform, material, prefab,
project, asset, scene, screenshot, profiler, session, command
```

Any command with a namespace not in this list → `custom`.

This list is maintained in one place in `cs.py` (or `__init__.py`) as a constant. When the Unity package adds new builtin namespaces, the list is updated in the next plugin release.

---

## Change 1: `list-commands --type` filtering

Add a `--type` flag to the existing `list-commands` subcommand:

```bash
cs list-commands --json                 # all commands (backward compatible)
cs list-commands --type custom --json   # only custom commands
cs list-commands --type builtin --json  # only builtin commands
```

Implementation: query the live editor, apply namespace-based filter, return filtered result.

---

## Change 2: Persistent catalog

### Storage

`{plugin_root}/catalog/{project_hash}.json`
- Per-project isolation (different Unity projects have different custom commands)
- `project_hash` = first 8 chars of SHA-256 of project root absolute path
- `catalog/` directory is git-ignored

### Schema

```json
{
  "version": 1,
  "project": "E:/UnityProjects/MyGame",
  "discovered_at": "2026-04-15T15:30:00Z",
  "commands": [
    {
      "id": "mymod.do_thing",
      "namespace": "mymod",
      "action": "do_thing",
      "summary": "...",
      "editorOnly": false,
      "args": [
        {"name": "target", "typeName": "String"}
      ]
    }
  ]
}
```

Catalog stores **custom commands only** (builtin commands are already in SKILL.md).

### `cs catalog` subcommand

```bash
cs catalog sync --json   # Query live editor → filter custom → diff against stored → update → output changes
cs catalog list --json   # Read stored catalog (offline, no Unity connection needed)
```

**`catalog sync` output:**

```json
{
  "ok": true,
  "summary": "Catalog updated: 2 added, 1 removed",
  "data": {
    "added": ["mymod.new_action"],
    "removed": ["mymod.old_action"],
    "changed": [],
    "total": 12
  }
}
```

---

## Change 3: `cs status --json`

Structured JSON output when `--json` flag is used:

```json
{
  "ok": true,
  "summary": "Connected to Unity 2022.3.20f1 (EditMode)",
  "data": {
    "project": {"path": "E:/UnityProjects/MyGame", "detected": true},
    "package": {"installed": true, "version": "1.3.1", "location": "manifest"},
    "service": {"reachable": true, "port": 14500, "mode": "editor"},
    "editor": {"state": "EditMode", "compiling": false, "refreshing": false},
    "versions": {
      "plugin": "1.3.1",
      "package": "1.3.1",
      "aligned": true
    },
    "commands": {"builtin": 73, "custom": 12}
  }
}
```

Sources:
- `project` / `package` — from existing `find_project_root()` and `find_package_dir()`
- `service` / `editor` — from existing `health()` response
- `versions` — from existing `version_check.check_versions()`
- `commands` — from `list-commands` with namespace-based classification

Text output (no `--json`) remains unchanged.

---

## Change 4: Skill & slash command updates

### `/unity-cli-refresh-commands`

Rewrite to call `cs catalog sync` instead of manual list + filter + write Markdown.

### Skill command lookup order

1. Check static builtin catalog in SKILL.md (73 commands)
2. Check per-project catalog JSON (custom commands)
3. If no catalog → fallback to `cs list-commands --json` live query
4. Suggest `/unity-cli-refresh-commands` if catalog missing

### `dynamic-commands.md` removal

Replaced by catalog JSON. The slash command no longer writes Markdown.

---

## Change 5: Documentation fixes

### CLAUDE.md

- Fix command count: 59 → actual count from SKILL.md
- Add `cs catalog` to command table

### README (EN + CN)

- Add catalog to feature list
- Update command table

---

## Scope Boundaries

- **No Unity C# package changes.** All changes are CLI/plugin side only.
- **No new error codes.** Existing `type` field is sufficient.
- **No protocol version changes.** CLI works with any package version.
- **No breaking changes.** All changes are additive.

---

## Deliverables

| Change | Files |
|--------|-------|
| `list-commands --type` | `cli/cs.py` |
| Persistent catalog | `cli/cs.py`, `cli/__init__.py`, `.gitignore` |
| `status --json` | `cli/cs.py` |
| Skill integration | `commands/unity-cli-refresh-commands.md`, `skills/unity-cli-command/SKILL.md` |
| Doc fixes | `CLAUDE.md`, `README.md`, `README_zh.md` |

## Execution Timeline

| Phase | Deliverables |
|-------|-------------|
| D0 (half day) | `list-commands --type`, builtin namespace constant, `cs catalog sync/list` |
| D1 (half day) | `cs status --json`, slash command update, skill integration |
| D2 (half day) | CLAUDE.md fix, README updates, testing |
