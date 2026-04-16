# Custom Command Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `commandType` to the Unity C# package, then build CLI-side filtering, persistent catalog, and structured status output in the plugin.

**Architecture:** Unity package gets 3 tiny additions (~20 lines): `CommandType` enum, `commandType` on attribute + descriptor, `isCompiling`/`compileErrorCount` on health. CLI plugin gets `list-commands --type`, `cs catalog sync/list`, `cs status --json`, and slash command rewrites. Both repos bump to 1.4.0.

**Tech Stack:** C# (Unity 2022.3+), Python 3.7+ (stdlib only)

**Spec:** `docs/superpowers/specs/2026-04-12-custom-command-enhancement-design.md`

**Two repos:**
- Unity C# package: `E:/UnityProjects/com.zh1zh1.csharpconsole`
- CLI plugin: `E:/UnityProjects/unity-cli-plugin`

---

### Task 1: Unity — Add `CommandType` enum and `commandType` to attribute

**Files:**
- Create: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/Commands/Core/CommandType.cs`
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/Commands/Routing/CommandActionAttribute.cs`

- [ ] **Step 1: Create `CommandType.cs`**

```csharp
namespace Zh1Zh1.CSharpConsole.Service.Commands.Core
{
    public enum CommandType
    {
        Builtin,
        Custom
    }
}
```

- [ ] **Step 2: Add `commandType` property to `CommandActionAttribute`**

In `CommandActionAttribute.cs`, add the property and constructor parameter:

```csharp
public sealed class CommandActionAttribute : Attribute
{
    public string commandNamespace { get; }
    public string action { get; }
    public bool editorOnly { get; }
    public bool runOnMainThread { get; }
    public string summary { get; }
    public CommandType commandType { get; }   // ADD

    public CommandActionAttribute(
        string commandNamespace,
        string action,
        bool editorOnly = false,
        bool runOnMainThread = true,
        string summary = "",
        CommandType commandType = CommandType.Builtin)   // ADD
    {
        this.commandNamespace = commandNamespace ?? "";
        this.action = action ?? "";
        this.editorOnly = editorOnly;
        this.runOnMainThread = runOnMainThread;
        this.summary = summary ?? "";
        this.commandType = commandType;   // ADD
    }
}
```

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/com.zh1zh1.csharpconsole
git add Runtime/Service/Commands/Core/CommandType.cs Runtime/Service/Commands/Routing/CommandActionAttribute.cs
git commit -m "feat: add CommandType enum and commandType to CommandActionAttribute"
```

---

### Task 2: Unity — Add `commandType` to `CommandDescriptor` and `CommandRouter`

**Files:**
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/Commands/Core/CommandDescriptor.cs`
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/Commands/Routing/CommandRouter.cs`

- [ ] **Step 1: Add field to `CommandDescriptor`**

In `CommandDescriptor.cs`, add one field after `runOnMainThread`:

```csharp
public string commandType = "builtin";
```

- [ ] **Step 2: Populate in `CommandRouter.BuildDescriptor()`**

In `CommandRouter.cs` line ~185, add to the object initializer:

```csharp
commandType = attribute.commandType == CommandType.Custom ? "custom" : "builtin",
```

Add the using directive at the top of the file:

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
```

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/com.zh1zh1.csharpconsole
git add Runtime/Service/Commands/Core/CommandDescriptor.cs Runtime/Service/Commands/Routing/CommandRouter.cs
git commit -m "feat: populate commandType in command list response"
```

---

### Task 3: Unity — Add `isCompiling` and `compileErrorCount` to health response

**Files:**
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/Contracts/HealthContracts.cs`
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/ConsoleHttpService.cs`

- [ ] **Step 1: Add fields to `HealthResponse`**

In `HealthContracts.cs`, add two fields to `HealthResponse` (after `unityVersion`):

```csharp
public bool isCompiling;
public int compileErrorCount;
```

- [ ] **Step 2: Populate in `BuildHealthResponseSnapshot()`**

In `ConsoleHttpService.cs` at `BuildHealthResponseSnapshot()` (line ~473), add inside the object initializer before `operation = state`:

```csharp
#if UNITY_EDITOR
isCompiling = UnityEditor.EditorApplication.isCompiling,
compileErrorCount = UnityEditor.Compilation.CompilationPipeline.GetPrecompiledAssemblyPaths().Length > 0
    ? 0  // placeholder — see step 3
    : 0,
#endif
```

Actually, `CompilationPipeline` does not directly expose error counts. Use `EditorUtility` log entries instead. The simplest reliable approach:

```csharp
#if UNITY_EDITOR
isCompiling = UnityEditor.EditorApplication.isCompiling,
compileErrorCount = GetCompileErrorCount(),
#endif
```

Add a helper method:

```csharp
#if UNITY_EDITOR
private static int GetCompileErrorCount()
{
    var flags = UnityEditor.Compilation.CompilationPipeline.GetCompilationTasks();
    // Simplest: count log entries of type Error
    int count = 0;
    var entries = UnityEditor.Compilation.CompilationPipeline.GetPrecompiledAssemblyPaths()?.Length ?? 0;
    // Alternative: use LogEntries if available
    try
    {
        var logEntriesType = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.LogEntries");
        if (logEntriesType != null)
        {
            var getCount = logEntriesType.GetMethod("GetCount", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public);
            if (getCount != null)
            {
                // LogEntries stores counts per type: 0=error, 1=warning, 2=log
                // But the API varies by Unity version. Safest: just check isCompiling.
            }
        }
    }
    catch { }
    return count;
}
#endif
```

**Note:** Getting exact compile error counts is Unity-version-dependent. The implementer should check what API is available in Unity 2022.3. The simplest approach that works across versions:

```csharp
#if UNITY_EDITOR
isCompiling = UnityEditor.EditorApplication.isCompiling,
compileErrorCount = UnityEditor.EditorUtility.scriptCompilationFailed ? -1 : 0,
#endif
```

Where `-1` means "there are errors but count unknown", `0` means "no errors". The implementer should investigate `CompilationPipeline.GetCompilationMessages()` (Unity 2022.3+) for exact counts if available.

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/com.zh1zh1.csharpconsole
git add Runtime/Service/Contracts/HealthContracts.cs Runtime/Service/ConsoleHttpService.cs
git commit -m "feat: add isCompiling and compileErrorCount to health response"
```

---

### Task 4: Unity — Bump version to 1.4.0

**Files:**
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/package.json` (version field)
- Modify: `E:/UnityProjects/com.zh1zh1.csharpconsole/Runtime/Service/ConsoleServiceConfig.cs` (PackageVersion constant)

- [ ] **Step 1: Update `package.json` version to `"1.4.0"`**

- [ ] **Step 2: Update `ConsoleServiceConfig.PackageVersion` to `"1.4.0"`**

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/com.zh1zh1.csharpconsole
git add package.json Runtime/Service/ConsoleServiceConfig.cs
git commit -m "chore: bump version to 1.4.0"
```

---

### Task 5: CLI — Add `--type` flag to `list-commands`

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/cli/cs.py`

- [ ] **Step 1: Add `--type` argument to `list-commands` subparser**

Replace line 418:
```python
sub.add_parser("list-commands", parents=[shared], help="List available commands")
```

With:
```python
sp_lc = sub.add_parser("list-commands", parents=[shared], help="List available commands")
sp_lc.add_argument("--type", choices=["builtin", "custom", "all"], default="all",
                    help="Filter by command type (default: all)")
```

- [ ] **Step 2: Add filtering logic to the dispatch**

Replace line 500:
```python
"list-commands": lambda: s.list_commands(),
```

With:
```python
"list-commands": lambda: _list_commands_filtered(s, args),
```

Add the filter function before `main()`:

```python
def _filter_commands_by_type(result, type_filter):
    """Filter list-commands result by commandType field."""
    if type_filter == "all":
        return result
    data = result.get("data", {})
    rj = data.get("resultJson", data)
    if isinstance(rj, str):
        import json as _json
        try:
            rj = _json.loads(rj)
        except (ValueError, TypeError):
            return result
    commands = rj.get("commands", [])
    filtered = [c for c in commands if c.get("commandType", "builtin") == type_filter]
    rj["commands"] = filtered
    if isinstance(data.get("resultJson"), str):
        data["resultJson"] = json.dumps(rj)
    else:
        data["commands"] = filtered
    return result
```

And inside `main()`, before the dispatch dict:

```python
def _list_commands_filtered(session, a):
    r = session.list_commands()
    return _filter_commands_by_type(r, a.type)
```

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add cli/cs.py
git commit -m "feat: add --type filter to list-commands"
```

---

### Task 6: CLI — Add `cs catalog sync` and `cs catalog list`

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/cli/cs.py` (argparse + handlers)
- Modify: `E:/UnityProjects/unity-cli-plugin/cli/__init__.py` (catalog path helpers)
- Modify: `E:/UnityProjects/unity-cli-plugin/.gitignore` (add `catalog/`)

- [ ] **Step 1: Add catalog path helpers to `cli/__init__.py`**

Append to `cli/__init__.py`:

```python
import hashlib

_CATALOG_DIR = _PLUGIN_DIR / "catalog"


def catalog_path(project_root):
    """Return the catalog JSON path for a given Unity project root."""
    h = hashlib.sha256(str(Path(project_root).resolve()).encode()).hexdigest()[:8]
    return _CATALOG_DIR / f"{h}.json"
```

- [ ] **Step 2: Add `catalog/` to `.gitignore`**

Add `catalog/` line to `.gitignore`.

- [ ] **Step 3: Add catalog subparser to `cs.py`**

After the `check-update` subparser (line 429), add:

```python
sp_cat = sub.add_parser("catalog", parents=[shared], help="Manage custom command catalog")
cat_sub = sp_cat.add_subparsers(dest="catalog_cmd")
cat_sub.add_parser("sync", parents=[shared], help="Sync catalog from live editor")
cat_sub.add_parser("list", parents=[shared], help="List cached catalog")
```

- [ ] **Step 4: Add catalog handlers**

Add two functions before `main()`:

```python
def cmd_catalog_sync(root, args, agent_root=None):
    """Query live editor for commands, filter custom, diff and persist."""
    from cli.core_bridge import find_package_dir, ConsoleSession
    pkg_dir = find_package_dir(root, agent_root)
    if pkg_dir is None:
        print("Error: package not found. Run 'cs setup' first.", file=sys.stderr)
        return 1
    s = ConsoleSession(root, args.ip, args.port, args.mode, args.timeout, pkg_dir=pkg_dir,
                       editor_port=getattr(args, "editor_port", None))
    r = s.list_commands()
    if not r.get("ok"):
        if args.as_json:
            json.dump(r, sys.stdout, ensure_ascii=False, indent=2)
            print()
        else:
            print(f"Error: {r.get('summary', 'list-commands failed')}", file=sys.stderr)
        return 1

    data = r.get("data", {})
    rj = data.get("resultJson", data)
    if isinstance(rj, str):
        rj = json.loads(rj)
    all_cmds = rj.get("commands", [])
    custom = [c for c in all_cmds if c.get("commandType", "builtin") == "custom"]

    # Load existing catalog for diff
    from cli import catalog_path
    cat_file = catalog_path(root)
    old_ids = set()
    if cat_file.is_file():
        try:
            old_cat = json.loads(cat_file.read_text("utf-8"))
            old_ids = {c["id"] for c in old_cat.get("commands", [])}
        except (json.JSONDecodeError, KeyError):
            pass

    new_ids = set()
    catalog_commands = []
    for c in custom:
        cid = f"{c.get('commandNamespace', '')}.{c.get('action', '')}"
        new_ids.add(cid)
        catalog_commands.append({
            "id": cid,
            "namespace": c.get("commandNamespace", ""),
            "action": c.get("action", ""),
            "summary": c.get("summary", ""),
            "editorOnly": c.get("editorOnly", False),
            "args": c.get("arguments", []),
        })

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)

    from datetime import datetime, timezone
    catalog = {
        "version": 1,
        "project": str(Path(root).resolve()),
        "discovered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commands": catalog_commands,
    }
    cat_file.parent.mkdir(parents=True, exist_ok=True)
    cat_file.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", "utf-8")

    result = {
        "ok": True, "exitCode": 0,
        "summary": f"Catalog updated: {len(added)} added, {len(removed)} removed",
        "data": {"added": added, "removed": removed, "total": len(catalog_commands)},
    }
    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(result["summary"])
        if added:
            print(f"  added: {', '.join(added)}")
        if removed:
            print(f"  removed: {', '.join(removed)}")
    return 0


def cmd_catalog_list(root, args):
    """Read and output the stored catalog."""
    from cli import catalog_path
    cat_file = catalog_path(root)
    if not cat_file.is_file():
        msg = "No catalog found. Run 'cs catalog sync' first."
        if args.as_json:
            json.dump({"ok": False, "exitCode": 1, "summary": msg}, sys.stdout, ensure_ascii=False, indent=2)
            print()
        else:
            print(msg)
        return 1

    catalog = json.loads(cat_file.read_text("utf-8"))
    if args.as_json:
        json.dump({"ok": True, "exitCode": 0, "summary": f"{len(catalog.get('commands', []))} custom commands",
                    "data": catalog}, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        cmds = catalog.get("commands", [])
        print(f"{len(cmds)} custom commands (discovered {catalog.get('discovered_at', '?')})")
        for c in cmds:
            print(f"  {c['namespace']}.{c['action']} — {c.get('summary', '')}")
    return 0
```

- [ ] **Step 5: Wire catalog into dispatch**

In `main()`, add after the `check-update` dispatch (line ~464):

```python
if args.cmd == "catalog":
    if root is None:
        print("Error: no Unity project found.", file=sys.stderr)
        sys.exit(1)
    if args.catalog_cmd == "sync":
        sys.exit(cmd_catalog_sync(root, args, agent_root))
    elif args.catalog_cmd == "list":
        sys.exit(cmd_catalog_list(root, args))
    else:
        sp_cat.print_help()
        sys.exit(1)
```

- [ ] **Step 6: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add cli/cs.py cli/__init__.py .gitignore
git commit -m "feat: add cs catalog sync/list for persistent custom command storage"
```

---

### Task 7: CLI — Add `cs status --json`

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/cli/cs.py` (`cmd_status` function)

- [ ] **Step 1: Add JSON branch to `cmd_status()`**

At the top of `cmd_status()` (line 277), add a JSON path after checking `root`:

```python
def cmd_status(root, args, agent_root=None):
    if args.as_json:
        return _cmd_status_json(root, args, agent_root)
    # ... existing text output below unchanged ...
```

- [ ] **Step 2: Add `_cmd_status_json()` function**

Add before `cmd_status`:

```python
def _cmd_status_json(root, args, agent_root=None):
    result = {"project": {"path": None, "detected": False}}
    if root is None:
        json.dump({"ok": False, "exitCode": 1, "summary": "No Unity project found",
                    "data": result}, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 1

    result["project"] = {"path": str(root), "detected": True}

    from cli.core_bridge import find_package_dir
    pkg_dir = find_package_dir(root, agent_root)
    result["package"] = {"installed": pkg_dir is not None}
    if pkg_dir:
        result["package"]["location"] = "manifest"
        # Read package version
        try:
            from cli.version_check import get_package_version
            result["package"]["version"] = get_package_version(pkg_dir) or "unknown"
        except Exception:
            result["package"]["version"] = "unknown"

    service = {"reachable": False}
    editor = {}
    if pkg_dir:
        from cli.core_bridge import ConsoleSession
        try:
            s = ConsoleSession(root, args.ip, args.port, args.mode, args.timeout, pkg_dir=pkg_dir,
                              editor_port=getattr(args, "editor_port", None))
            r = s.health()
            if r.get("ok"):
                d = r.get("data", {})
                service = {"reachable": True, "port": args.port, "mode": args.mode}
                editor = {
                    "state": d.get("editorState", ""),
                    "compiling": d.get("isCompiling", False),
                    "refreshing": d.get("refreshing", False),
                    "compileErrors": d.get("compileErrorCount", 0),
                }
        except Exception:
            pass

    result["service"] = service
    if editor:
        result["editor"] = editor

    # Version alignment
    versions = {}
    try:
        from cli.version_check import get_plugin_version, get_package_version, is_aligned
        pv = get_plugin_version()
        kv = get_package_version(pkg_dir) if pkg_dir else None
        versions = {"plugin": pv, "package": kv, "aligned": is_aligned(pv, kv) if kv else None}
    except Exception:
        pass
    if versions:
        result["versions"] = versions

    # Command counts
    if service.get("reachable") and pkg_dir:
        try:
            r = s.list_commands()
            if r.get("ok"):
                data = r.get("data", {})
                rj = data.get("resultJson", data)
                if isinstance(rj, str):
                    rj = json.loads(rj)
                cmds = rj.get("commands", [])
                builtin = sum(1 for c in cmds if c.get("commandType", "builtin") == "builtin")
                custom = sum(1 for c in cmds if c.get("commandType", "builtin") == "custom")
                result["commands"] = {"builtin": builtin, "custom": custom}
        except Exception:
            pass

    summary_parts = []
    if service.get("reachable") and editor.get("state"):
        summary_parts.append(f"Connected to Unity ({editor['state']})")
    elif service.get("reachable"):
        summary_parts.append("Connected")
    else:
        summary_parts.append("Service unreachable")

    json.dump({"ok": service.get("reachable", False), "exitCode": 0,
               "summary": " ".join(summary_parts),
               "data": result}, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0
```

- [ ] **Step 3: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add cli/cs.py
git commit -m "feat: add structured JSON output for cs status --json"
```

---

### Task 8: CLI — Update `/unity-cli-refresh-commands` slash command

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/commands/unity-cli-refresh-commands.md`

- [ ] **Step 1: Rewrite the slash command**

Replace the full contents of `commands/unity-cli-refresh-commands.md` with:

```markdown
---
description: "Refresh cached custom command list from Unity"
---

Sync the custom command catalog from the running Unity Editor.

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" catalog sync --json --project "$(pwd)"
```

Parse the JSON output. Report the summary (added/removed/total).

If the command fails, suggest the user check that Unity Editor is open and the C# Console package is installed.
```

- [ ] **Step 2: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add commands/unity-cli-refresh-commands.md
git commit -m "feat: rewrite /unity-cli-refresh-commands to use cs catalog sync"
```

---

### Task 9: CLI — Update SKILL.md custom command discovery section

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/skills/unity-cli-command/SKILL.md`

- [ ] **Step 1: Update the custom commands section**

Find the section that references `dynamic-commands.md` and update it to reference the catalog JSON. The lookup order should be:

1. Check static builtin catalog in SKILL.md (the table above)
2. Check per-project catalog JSON at `${CLAUDE_PLUGIN_ROOT}/catalog/*.json`
3. If no catalog → fallback to `cs list-commands --type custom --json` live query
4. Suggest `/unity-cli-refresh-commands` if catalog missing

Also add `cs catalog sync` and `cs catalog list` to the command reference section, and document the `--type` flag for `list-commands`.

- [ ] **Step 2: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add skills/unity-cli-command/SKILL.md
git commit -m "docs: update SKILL.md for catalog-based custom command discovery"
```

---

### Task 10: CLI — Update CLAUDE.md and bump version

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/CLAUDE.md`
- Modify: `E:/UnityProjects/unity-cli-plugin/.claude-plugin/plugin.json`

- [ ] **Step 1: Fix command count in CLAUDE.md**

Update the line that says `Built-in commands (59)` to match the actual count in SKILL.md.

- [ ] **Step 2: Add `cs catalog` to the command table in CLAUDE.md**

Add to the commands table:

```
| `cs catalog sync` | post | Sync custom command catalog from live editor |
| `cs catalog list` | post | List cached custom commands (offline) |
```

- [ ] **Step 3: Bump plugin version to 1.4.0 in `plugin.json`**

- [ ] **Step 4: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add CLAUDE.md .claude-plugin/plugin.json
git commit -m "chore: fix command count, add catalog to CLAUDE.md, bump to 1.4.0"
```

---

### Task 11: CLI — Update READMEs

**Files:**
- Modify: `E:/UnityProjects/unity-cli-plugin/README.md`
- Modify: `E:/UnityProjects/unity-cli-plugin/README_zh.md`

- [ ] **Step 1: Add catalog to feature list and command table in both READMEs**

Add `cs catalog sync/list` to the command table. Add a brief mention of persistent custom command catalog to the features section.

- [ ] **Step 2: Commit**

```bash
cd E:/UnityProjects/unity-cli-plugin
git add README.md README_zh.md
git commit -m "docs: add catalog commands to READMEs"
```
