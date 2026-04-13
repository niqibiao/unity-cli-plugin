# Custom Command Enhancement Design

## Overview

Comprehensive enhancement of the unity-cli-plugin and its companion Unity package (`com.zh1zh1.csharpconsole`) across 5 tracks + 1 cross-cutting concern. The goal is to make custom command authoring, discovery, and consumption a first-class workflow for Claude Code agents operating inside Unity.

## Current State

### What exists today

| Component | State |
|-----------|-------|
| `CommandActionAttribute` | 5 fields: `commandNamespace`, `action`, `editorOnly`, `runOnMainThread`, `summary` |
| `CommandDescriptor` (list-commands response) | `id`, `commandNamespace`, `action`, `summary`, `editorOnly`, `runOnMainThread`, `declaringType`, `methodName`, `arguments` |
| CLI `list-commands` | Passes through Unity response; no filtering or enrichment |
| Custom command cache | `dynamic-commands.md` — git-ignored Markdown table, single global file |
| Error model | `type` field with 3 values: `ok`, `validation_error`, `system_error` |
| Health endpoint | Rich: `ok`, `initialized`, `isEditor`, `port`, `refreshing`, `generation`, `editorState`, `packageVersion`, `protocolVersion`, `unityVersion`, `operation` |
| Diagnostics | `cs status` (text output) + `cs health` (JSON passthrough) |

### What's missing

- No way to distinguish builtin vs custom commands at the source (Unity side)
- No persistent per-project catalog — the Markdown cache is fragile and single-project
- No structured diagnostics (doctor) that can guide an agent through recovery
- Error codes are too coarse for agent-driven workflows
- No `--type` / `--origin` filtering on `list-commands`

---

## Track 1: Unity C# Package — Command Metadata Extension

### 1.1 `CommandActionAttribute` expansion

Add two optional properties to the existing attribute:

```csharp
[CommandAction("custom", "my_action",
    summary: "Description",
    commandType: CommandType.Custom,           // NEW — default: Builtin
    stability: CommandStability.Stable          // NEW — default: Stable
)]
```

**Enum definitions:**

```csharp
public enum CommandType
{
    Builtin,   // Ships with com.zh1zh1.csharpconsole
    Custom     // User-defined or third-party
}

public enum CommandStability
{
    Stable,
    Experimental
}
```

**Design rationale:**
- `commandType` is set by the command author, not inferred. Builtin handlers set `CommandType.Builtin`; third-party or user code sets `CommandType.Custom`.
- `stability` lets authors mark experimental commands so agents can prefer stable commands.
- `origin` (assembly name) is **not** an attribute field — it's derived at runtime via `DeclaringType.Assembly.GetName().Name` during command discovery. This avoids redundancy and stays accurate even after refactoring.

### 1.2 `CommandDescriptor` response expansion

Add 3 new fields to the JSON returned by `command/list`:

```json
{
  "id": "mymod.do_thing",
  "commandNamespace": "mymod",
  "action": "do_thing",
  "summary": "...",
  "editorOnly": false,
  "runOnMainThread": true,
  "declaringType": "MyGame.Editor.MyCommands",
  "methodName": "DoThing",
  "arguments": [...],
  "commandType": "custom",
  "origin": "MyGame.Editor",
  "stability": "stable"
}
```

| Field | Source | Type |
|-------|--------|------|
| `commandType` | `CommandActionAttribute.commandType` | `"builtin"` or `"custom"` |
| `origin` | `DeclaringType.Assembly.GetName().Name` at discovery time | string (assembly name) |
| `stability` | `CommandActionAttribute.stability` | `"stable"` or `"experimental"` |

### 1.3 Backward compatibility

- Both new `CommandActionAttribute` properties have defaults (`Builtin`, `Stable`), so existing `[CommandAction]` usage compiles without changes.
- Existing command handler classes in the package must be updated to explicitly set `commandType: CommandType.Builtin` (they already are builtin — this just makes it explicit).
- The `CommandDescriptor` JSON gains 3 new keys. Older CLI versions that don't read them are unaffected.

---

## Track 2: Unity C# Package — System Doctor Endpoint

### 2.1 New command: `system/doctor`

Register a new `[CommandAction("system", "doctor")]` that returns structured diagnostic checks:

```json
{
  "checks": [
    {"name": "unity_version", "status": "ok", "value": "2022.3.20f1"},
    {"name": "editor_state", "status": "ok", "value": "EditMode"},
    {"name": "domain_reload_pending", "status": "ok", "value": false},
    {"name": "compile_errors", "status": "fail", "value": 3, "suggestion": "Fix compile errors before executing commands"},
    {"name": "is_compiling", "status": "ok", "value": false},
    {"name": "is_refreshing", "status": "ok", "value": false},
    {"name": "repl_available", "status": "ok", "value": true},
    {"name": "active_sessions", "status": "ok", "value": 1},
    {"name": "registered_commands", "status": "ok", "value": {"builtin": 46, "custom": 12}},
    {"name": "package_version", "status": "ok", "value": "1.2.0"},
    {"name": "protocol_version", "status": "ok", "value": 1}
  ]
}
```

**Check contract:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Machine-readable check identifier |
| `status` | `"ok"` or `"warn"` or `"fail"` | Check result |
| `value` | any (optional) | Current value |
| `suggestion` | string (optional) | Recovery hint, only present when status != ok |

### 2.2 Implementation approach

The doctor endpoint aggregates data already available inside the Unity process:
- `EditorApplication.isCompiling`, `EditorApplication.isUpdating` → compile/refresh checks
- `CompilationPipeline.GetCompilationErrors()` or console log scan → compile error count
- Existing health response fields → editor state, version info
- `CommandRouter.GetRegisteredCommands()` → command counts by type

No new subsystems needed — this is a structured view over existing state.

---

## Track 3: Unity C# Package — Standardized Error Codes

### 3.1 Error code enum

Add a `CommandErrorCode` enum used in error responses:

```csharp
public enum CommandErrorCode
{
    // Validation errors
    CommandNotFound,        // namespace/action not registered
    InvalidArguments,       // args failed validation
    EditorOnlyViolation,    // editor-only command called from runtime

    // Execution errors
    CompileFailed,          // script compilation failure
    ExecFailed,             // C# code execution error
    DomainReloadInProgress, // domain reload active, cannot execute
    PlaymodeConflict,       // operation not allowed in current play mode state

    // System errors
    InternalError,          // unexpected exception
    Timeout                 // execution exceeded time limit
}
```

### 3.2 Error response format

Extend `CommandResponse` to include:

```json
{
  "ok": false,
  "type": "validation_error",
  "errorCode": "COMMAND_NOT_FOUND",
  "summary": "Command 'foo.bar' is not registered",
  "suggestion": "Run 'command list' to see available commands",
  "commandNamespace": "foo",
  "action": "bar"
}
```

| Field | Type | When present |
|-------|------|-------------|
| `errorCode` | string | Always when `ok == false` |
| `suggestion` | string | When a recovery action exists |

### 3.3 Backward compatibility

- `type` field remains (`ok`, `validation_error`, `system_error`) for backward compat
- `errorCode` is a new, more granular field — CLI versions that don't read it are unaffected
- Existing error paths in `CommandResponseFactory` are updated to include `errorCode` and `suggestion`

---

## Track 4: CLI — Typed Command Discovery & Persistent Catalog

### 4.1 `list-commands` enhancement

Add filtering flags to the existing `list-commands` CLI command:

```bash
# Default: list all commands (backward compatible)
cs list-commands --json

# Filter by type
cs list-commands --type custom --json
cs list-commands --type builtin --json

# Filter by origin assembly
cs list-commands --origin "MyGame.Editor" --json
```

**Backward compatibility:** If the Unity package response lacks `commandType` (older package version), the CLI falls back to namespace-list inference:
- Known builtin namespaces: `editor`, `gameobject`, `component`, `transform`, `material`, `prefab`, `project`, `asset`, `scene`, `screenshot`, `profiler`, `session`, `command`
- Everything else → `custom`

### 4.2 Persistent catalog

**Storage location:** `{plugin_root}/catalog/{project_hash}.json`
- Per-project isolation — different Unity projects have different custom commands
- `project_hash` = first 8 chars of SHA-256 of the project root absolute path
- The `catalog/` directory is git-ignored

**Catalog schema:**

```json
{
  "version": 1,
  "project": "E:/UnityProjects/MyGame",
  "discovered_at": "2026-04-12T15:30:00Z",
  "package_version": "1.2.0",
  "commands": [
    {
      "id": "mymod.do_thing",
      "namespace": "mymod",
      "action": "do_thing",
      "summary": "...",
      "commandType": "custom",
      "origin": "MyGame.Editor",
      "stability": "stable",
      "editorOnly": false,
      "args": [
        {"name": "target", "typeName": "String"}
      ]
    }
  ]
}
```

### 4.3 New CLI subcommand: `cs catalog`

```bash
cs catalog sync --json     # Query live → diff against stored → update → output changes
cs catalog list --json     # Read stored catalog (offline, no Unity connection needed)
cs catalog path            # Print the catalog file path for the current project
```

**`catalog sync` flow:**
1. Call `list-commands` against the live editor
2. Compare with stored catalog (if any)
3. Write updated catalog file
4. Return `{ "added": [...], "removed": [...], "changed": [...], "total": N }`

**`catalog list` flow:**
1. Resolve project root → compute hash → find catalog file
2. Read and return the stored catalog
3. If no catalog exists, return `{ "ok": false, "summary": "No catalog found. Run 'cs catalog sync' first." }`

### 4.4 Skill integration

The `dynamic-commands.md` mechanism is replaced:
- `$unity-cli-refresh-commands` now calls `cs catalog sync`
- The skill (`skills/unity-cli-command/SKILL.md`) reads the catalog JSON instead of `dynamic-commands.md`
- `dynamic-commands.md` is deleted (it was git-ignored, so no history impact)

Skill command lookup order:
1. Check static builtin catalog in SKILL.md (46 commands)
2. Check per-project catalog JSON (custom commands)
3. If no match → fallback to `cs list-commands --json` live query
4. Suggest `$unity-cli-refresh-commands` if catalog is stale

---

## Track 5: CLI — Enhanced Diagnostics

### 5.1 `cs status` enhancement

Output structure (JSON mode):

```json
{
  "ok": true,
  "summary": "Connected to Unity 2022.3.20f1 (EditMode)",
  "data": {
    "project": {"path": "E:/UnityProjects/MyGame", "detected": true},
    "package": {"installed": true, "version": "1.2.0", "location": "manifest"},
    "service": {"reachable": true, "port": 14500, "mode": "editor"},
    "editor": {"state": "EditMode", "compiling": false, "refreshing": false},
    "versions": {
      "plugin": "1.2.0",
      "package": "1.2.0",
      "aligned": true
    },
    "commands": {"builtin": 46, "custom": 12, "catalog_stale": false}
  }
}
```

**Changes from current status:**
- JSON output now structured (currently it's text-only for status)
- Includes command count and catalog freshness
- Includes compile/refresh state from health endpoint

### 5.2 New CLI command: `cs doctor`

Layered diagnostic checks, some client-side (no Unity connection needed), some server-side:

| Layer | Check | Needs service? | Source |
|-------|-------|---------------|--------|
| L0 | Project directory detected | No | `find_project_root()` |
| L1 | Package installed in manifest | No | `manifest.json` |
| L2 | Package files resolvable | No | `core_bridge.find_package_dir()` |
| L3 | Service reachable | Yes | `health()` |
| L4 | Version alignment | Yes | `health` response + `plugin.json` |
| L5 | Not compiling / not refreshing | Yes | `health` response |
| L6 | No compile errors | Yes | `system/doctor` endpoint |
| L7 | REPL available | Yes | `system/doctor` endpoint |
| L8 | Command catalog fresh | Yes | `system/doctor` + local catalog |

**Behavior:**
- Runs checks in order L0→L8
- If L3 fails (service unreachable), skips L4–L8 and reports clearly
- Each check outputs: `name`, `status` (ok/warn/fail), `message`, `suggestion` (if failed)
- Exit code: 0 if all pass, 1 if any fail

**Output (JSON mode):**

```json
{
  "ok": false,
  "summary": "5 passed, 0 warnings, 1 failed",
  "data": {
    "checks": [
      {"name": "project_detected", "status": "ok", "message": "E:/UnityProjects/MyGame"},
      {"name": "package_installed", "status": "ok", "message": "1.2.0 via manifest"},
      {"name": "package_resolvable", "status": "ok"},
      {"name": "service_reachable", "status": "ok", "message": "port 14500"},
      {"name": "version_aligned", "status": "ok"},
      {"name": "compile_errors", "status": "fail", "message": "3 compile errors", "suggestion": "Fix compile errors before executing commands"}
    ]
  }
}
```

---

## Track 6: Documentation & Skill Updates

### 6.1 SKILL.md updates

**`skills/unity-cli-command/SKILL.md`:**
- Add `cs catalog` subcommands to the command reference
- Update custom command discovery section to reference catalog JSON
- Document `--type` and `--origin` flags for `list-commands`

**`skills/unity-cli-exec-code/SKILL.md`:**
- Add guidance: check `cs doctor` when exec fails unexpectedly
- Reference error codes for common failure scenarios

### 6.2 Slash command updates

**`$unity-cli-refresh-commands`:**
- Rewrite to call `cs catalog sync` instead of manual list + filter + write
- Output the sync diff (added/removed/changed)

**`$unity-cli-status`:**
- Update to show the new structured status output

### 6.3 CLAUDE.md updates

- Add `cs catalog` and `cs doctor` to the command table
- Update the architecture diagram to show catalog flow
- Document error codes

### 6.4 README updates

Both EN and CN READMEs:
- Add catalog and doctor to feature list
- Add workflow examples section
- Update command table

---

## Cross-Cutting: Error Model

### End-to-end error flow

```
Unity C# (throw / CommandResponseFactory)
  → HTTP Response (JSON body with errorCode + suggestion)
    → Python CLI (parse errorCode, map to exit code, format output)
      → Claude (structured JSON for agent / human-readable text for terminal)
```

### Error code mapping

| Error Code | CLI Layer | Unity Layer | Exit Code |
|------------|----------|-------------|-----------|
| `PROJECT_NOT_FOUND` | CLI | — | 1 |
| `PACKAGE_NOT_FOUND` | CLI | — | 1 |
| `SERVICE_UNREACHABLE` | CLI | — | 1 |
| `PORT_DETECTION_FAILED` | CLI | — | 1 |
| `VERSION_MISMATCH` | CLI | — | 0 (warning) |
| `COMMAND_NOT_FOUND` | — | Unity | 1 |
| `INVALID_ARGUMENTS` | — | Unity | 1 |
| `EDITOR_ONLY_VIOLATION` | — | Unity | 1 |
| `COMPILE_FAILED` | — | Unity | 1 |
| `EXEC_FAILED` | — | Unity | 1 |
| `DOMAIN_RELOAD_IN_PROGRESS` | — | Unity | 1 |
| `PLAYMODE_CONFLICT` | — | Unity | 1 |
| `INTERNAL_ERROR` | — | Unity | 1 |
| `TIMEOUT` | CLI | — | 1 |

### CLI-side error handling changes

- Parse `errorCode` from Unity responses when present
- Map to human-readable messages with recovery suggestions
- Maintain backward compat: if `errorCode` absent, fall back to `type` field classification

---

## Scope Boundaries — What This Does NOT Include

- **No new HTTP endpoints** beyond `system/doctor`. The existing `/command` endpoint handles all new commands.
- **No breaking changes** to existing CLI arguments or output format. All changes are additive.
- **No build system changes**. Both projects remain pure (no external deps in CLI, standard Unity package structure in C#).
- **No MCP changes**. The CLI-first architecture is preserved.
- **No auth/permissions**. The HTTP service remains local-only, no authentication.

---

## Deliverable Summary

| Track | Repo | Key Deliverables |
|-------|------|-----------------|
| 1 — Command Metadata | unity-csharpconsole | `CommandType` enum, `CommandStability` enum, `CommandActionAttribute` expansion, `CommandDescriptor` expansion |
| 2 — Doctor Endpoint | unity-csharpconsole | `system/doctor` command handler, `DoctorCheck` contract |
| 3 — Error Codes | unity-csharpconsole | `CommandErrorCode` enum, `CommandResponse` expansion, `CommandResponseFactory` updates |
| 4 — Discovery & Catalog | unity-cli-plugin | `list-commands --type/--origin`, `cs catalog` subcommand, per-project JSON catalog, skill integration |
| 5 — Diagnostics | unity-cli-plugin | `cs status --json` structured output, `cs doctor` command |
| 6 — Docs & Skills | unity-cli-plugin | SKILL.md, slash commands, CLAUDE.md, README updates |
| Cross — Error Model | both | End-to-end error code propagation |

## Execution Timeline

| Phase | Days | Core Deliverables |
|-------|------|------------------|
| D0 | 1 day | Design lock + Unity C# package: CommandType/Stability enums, attribute expansion, CommandDescriptor expansion |
| D1 | 1 day | Unity C#: doctor endpoint + error code standardization; CLI: list-commands filtering |
| D2 | 1 day | CLI: catalog subcommand + status/doctor; Plugin: update skills and slash commands |
| D3 | 1 day | Documentation: README rewrite, workflow examples, error recovery guide |
| D4 | 1 day | Integration testing + bug fixes + release notes |
