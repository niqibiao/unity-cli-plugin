---
name: unity-cli-exec-code
description: >
  Fallback for executing raw C# code in Unity when no framework command
  (unity-cli-command skill) covers the task. Check unity-cli-command first.
  Trigger words: "execute C#", "run code in Unity", "eval", or any explicit
  C# snippet the user provides.
  Also use for: custom editor scripting, AssetDatabase operations, complex
  queries spanning multiple APIs, reflection, private member inspection,
  LINQ scene queries, or any Unity API not covered by a framework command.
---

# Unity CLI Exec Code (Fallback)

Execute raw C# in a running Unity Editor via the Roslyn-based CSharpConsole REPL.
Always prefer the `unity-cli-command` skill first.

## Usage

```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" exec --json --project "$(pwd)" "<C# code>"
```

All examples below use this exact command, showing only the C# code portion for brevity.

## REPL Features

This is a Roslyn REPL, not a simple eval. Non-obvious capabilities:

- **Top-level syntax** — no `class`/`Main` boilerplate; write statements directly
- **Expression auto-return** — the last expression value is returned in the result; prefer over `Debug.Log`
- **Cross-submission state** — variables, `using`s, and types persist across `exec` calls within the session
- **Private member access** — compiler bypasses `private`/`protected`/`internal` at compile time
- **Pre-loaded usings** — `System` and `UnityEngine` are available by default. Add `using System.Linq;` or `using System.Collections.Generic;` explicitly when needed (they persist in the session)

## Patterns

### Expression evaluation

```csharp
DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
```

```csharp
var cam = Camera.main; cam.fieldOfView
```

### Multi-step with cross-submission state

```csharp
// Call 1: store a reference
var player = GameObject.Find("Player");
```

```csharp
// Call 2: `player` is still alive
player.transform.position
```

### Private member access (no reflection needed)

```csharp
var go = GameObject.Find("Main Camera"); go.m_InstanceID
```

### LINQ queries over live scene

```csharp
using System.Linq; GameObject.FindObjectsOfType<Rigidbody>().Select(r => $"{r.name}: mass={r.mass}").ToList()
```

```csharp
// System.Linq persists from the previous submission
Resources.FindObjectsOfTypeAll<GameObject>().Where(g => !g.activeInHierarchy).Select(g => g.name).ToList()
```

### AssetDatabase

```csharp
using System.Linq; UnityEditor.AssetDatabase.FindAssets("t:Material").Select(g => UnityEditor.AssetDatabase.GUIDToAssetPath(g)).ToList()
```

### Define reusable helpers (persists in session)

```csharp
// Call 1: define
string Dump(Transform t, int d=0) { var s = new string(' ', d*2) + t.name; foreach(Transform c in t) s += "\n" + Dump(c, d+1); return s; }
```

```csharp
// Call 2: use
Dump(GameObject.Find("Canvas").transform)
```

### Batch modify

```csharp
foreach(var r in GameObject.FindGameObjectsWithTag("Debug").SelectMany(g => g.GetComponents<MeshRenderer>())) r.enabled = false;
```

## Session Reset

Reset when variable name collisions or stale state occur:

```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" command --json --project "$(pwd)" session reset
```

## Notes

- Always use `--json` for parseable output
- Check `result.ok` and `result.exitCode` for success/failure
- Port is auto-detected from `Temp/CSharpConsole/refresh_state.json`
