# Custom Command Enhancement Design

## Overview

Enhance custom command discovery and consumption across both repos. Unity C# package gets minimal metadata changes (~20 lines); CLI plugin gets catalog, filtering, and status improvements.

## Current State

| Component | Repo | State |
|-----------|------|-------|
| `CommandActionAttribute` | csharpconsole | 5 fields: `commandNamespace`, `action`, `editorOnly`, `runOnMainThread`, `summary` — no `commandType` |
| `CommandDescriptor` | csharpconsole | 9 fields — no `commandType` |
| Health response | csharpconsole | Has `refreshing`, `editorState`, but no `isCompiling`, `compileErrorCount` |
| CLI `list-commands` | cli-plugin | Passes through Unity response; no filtering |
| Custom command cache | cli-plugin | `dynamic-commands.md` — git-ignored Markdown table |
| `cs status` | cli-plugin | Text-only output; no `--json` |
| Built-in command count | cli-plugin | 73 in SKILL.md (CLAUDE.md says 59 — outdated) |
| Both repos version | both | 1.3.1 |

---

## Unity C# Package Changes (minimal)

### U1. `CommandActionAttribute` — add `commandType`

```csharp
public enum CommandType { Builtin, Custom }

[CommandAction("custom", "my_action",
    summary: "Description",
    commandType: CommandType.Custom  // NEW — default: Builtin
)]
```

Default is `Builtin`, so existing `[CommandAction]` usage compiles without changes.

### U2. `CommandDescriptor` — add `commandType` field

One new field in the JSON returned by `command/list`:

```json
{
  "commandType": "custom"
}
```

Populated from the attribute value during command registration in `CommandRouter`.

### U3. Health response — add `isCompiling` and `compileErrorCount`

```json
{
  "isCompiling": false,
  "compileErrorCount": 0
}
```

Sources: `EditorApplication.isCompiling` and `CompilationPipeline`.

These let agents decide whether to wait before executing commands.

### U4. Version requirement

Both repos release together. CLI plugin 1.4.0 requires Unity package >= 1.4.0. No fallback for older package versions.

---

## CLI Plugin Changes

### C1. `list-commands --type` filtering

```bash
cs list-commands --json                 # all commands (backward compatible)
cs list-commands --type custom --json   # only custom commands
cs list-commands --type builtin --json  # only builtin commands
```

Uses `commandType` field from Unity response directly. No namespace-list inference.

### C2. Persistent catalog

**Storage:** `{plugin_root}/catalog/{project_hash}.json`
- Per-project isolation
- `project_hash` = first 8 chars of SHA-256 of project root path
- `catalog/` is git-ignored

**Schema:**

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

Stores **custom commands only** (builtin commands are in SKILL.md).

**Subcommand:**

```bash
cs catalog sync --json   # Query live → filter custom → diff → update → output changes
cs catalog list --json   # Read stored catalog (offline)
```

### C3. `cs status --json`

```json
{
  "ok": true,
  "summary": "Connected to Unity 2022.3.20f1 (EditMode)",
  "data": {
    "project": {"path": "E:/UnityProjects/MyGame", "detected": true},
    "package": {"installed": true, "version": "1.3.1", "location": "manifest"},
    "service": {"reachable": true, "port": 14500, "mode": "editor"},
    "editor": {"state": "EditMode", "compiling": false, "refreshing": false, "compileErrors": 0},
    "versions": {"plugin": "1.3.1", "package": "1.3.1", "aligned": true},
    "commands": {"builtin": 73, "custom": 12}
  }
}
```

`editor.compiling` and `editor.compileErrors` sourced from the new health fields (U3). If unavailable (older package), omitted.

Text output remains unchanged.

### C4. Skill & slash command updates

- `/unity-cli-refresh-commands` → calls `cs catalog sync`
- `dynamic-commands.md` → replaced by catalog JSON
- Skill lookup: SKILL.md (builtin) → catalog JSON (custom) → live query fallback

### C5. Documentation fixes

- CLAUDE.md: fix command count, add `cs catalog`
- README (EN + CN): add catalog, update command table

---

## Scope Boundaries

- **No new endpoints.** `commandType` goes through existing `command/list`.
- **No error code changes.** Existing `type` field is sufficient.
- **No breaking changes.** All additions are additive with defaults.

---

## Deliverables

| Change | Repo | Files |
|--------|------|-------|
| U1-U2: commandType | csharpconsole | `CommandActionAttribute.cs`, `CommandDescriptor.cs`, `CommandRouter.cs` |
| U3: health fields | csharpconsole | `HealthContracts.cs`, `HealthEndpointHandler.cs` |
| C1: list-commands --type | cli-plugin | `cli/cs.py` |
| C2: catalog | cli-plugin | `cli/cs.py`, `cli/__init__.py`, `.gitignore` |
| C3: status --json | cli-plugin | `cli/cs.py` |
| C4: skill integration | cli-plugin | `commands/unity-cli-refresh-commands.md`, `skills/unity-cli-command/SKILL.md` |
| C5: docs | cli-plugin | `CLAUDE.md`, `README.md`, `README_zh.md` |

## Execution Timeline

| Phase | Deliverables |
|-------|-------------|
| D0 (half day) | Unity C#: U1-U3 (~20 lines total) |
| D1 (half day) | CLI: `list-commands --type`, `cs catalog sync/list` |
| D2 (half day) | CLI: `cs status --json`, slash command + skill update, docs |
