# unity-cli-plugin

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Unity 2022.3+](https://img.shields.io/badge/Unity-2022.3%2B-blue.svg)](https://unity.com/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet.svg)](https://claude.ai/code)

English | [中文](README_zh.md)

> **Depends on [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)** — A Roslyn-powered interactive C# REPL for Unity with cross-submission state, private member access, semantic completion, remote runtime execution (IL2CPP via HybridCLR), and an extensible command framework.

---

A [Claude Code](https://claude.ai/code) plugin for Unity Editor — 40+ commands for scene editing, components, assets, screenshots, profiling, and more. Powered by [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole).

```
You:    "Create 10 cubes in a circle and add Rigidbody to each"
Claude: Done. 10 cubes created at radius 5, each with a Rigidbody component.
```

### CLI + Skills, Not MCP

Same approach as [Playwright CLI](https://github.com/microsoft/playwright-cli) — CLI commands exposed through Claude Code's skill system instead of MCP. Why:

- **Token-efficient.** Skills load on demand; MCP loads all tool schemas on every request.
- **Unrestricted.** Falls back to a full [Roslyn C# REPL](https://github.com/niqibiao/unity-csharpconsole) — not limited to predefined tools.
- **No sidecar.** Service runs inside Unity Editor. No extra process.
- **Workflow-aware.** Understands Unity's compile lifecycle, play mode, domain reload.

| | CLI + Skills (this plugin) | MCP |
|-|:--------------------------:|:---:|
| Context window cost | **Low** (on-demand) | High (always loaded) |
| C# REPL fallback | **Yes** | Limited or none |
| External server | **None** (in-process) | Required |
| Play-mode-aware refresh | **Yes** | No |
| Custom command discovery | **Automatic** | Manual registration |
| Runtime / IL2CPP | **Yes** (HybridCLR) | Varies |

### Quick Start

**Prerequisites:** [Claude Code](https://claude.ai/code), Unity 2022.3+, Python 3.7+

```bash
# 1. Install the plugin
claude plugin install github:niqibiao/unity-cli-plugin

# 2. Install the Unity package (inside your project)
claude
> /unity-cli-setup

# 3. Verify
> /unity-cli-status
```

### Usage

Just tell Claude what you want:

```
> Add a directional light and rotate it 45 degrees on X
> Find all "Enemy" objects and list their components
> Take a screenshot of the Scene View
> Start profiler recording with deep profiling
```

Claude picks the right command or writes C# code as needed.

#### Slash Commands

| Command | Description |
|---------|-------------|
| `/unity-cli-setup` | Install the Unity package |
| `/unity-cli-status` | Check package and service status |
| `/unity-cli-refresh` | Trigger asset refresh / recompile |
| `/unity-cli-refresh-commands` | Refresh cached custom command list |

#### Direct CLI

```bash
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'
python cli/cs.py refresh --json --project . --wait 60
python cli/cs.py list-commands --json --project .
```

### Commands

46 commands across 12 namespaces. All commands support `--json` output.

**gameobject** — `find`, `create`, `destroy`, `get`, `modify`, `set-parent`, `duplicate`

**component** — `add`, `remove`, `get`, `modify`

**transform** — `get`, `set` (position/rotation/scale, local or world)

**scene** — `hierarchy` (full tree with optional components)

**prefab** — `create`, `instantiate`, `unpack`

**material** — `create`, `get`, `assign`

**screenshot** — `scene-view`, `game-view`

**profiler** — `start`, `stop`, `status`, `save`

**editor** — `status`, `playmode.status`, `playmode.enter`, `playmode.exit`, `menu.open`, `window.open`, `console.get`, `console.clear`

**project** — `scene.list`, `scene.open`, `scene.save`, `selection.get`, `selection.set`, `asset.list`, `asset.import`, `asset.reimport`

**session** — `list`, `inspect`, `reset`

**command** — `list`

<details>
<summary>Full command reference with args</summary>

| Command | Args |
|---------|------|
| `gameobject/find` | `name`, `tag`, `componentType` |
| `gameobject/create` | `name`, `primitiveType`, `parentPath` |
| `gameobject/destroy` | `path`, `instanceId` |
| `gameobject/get` | `path`, `instanceId` |
| `gameobject/modify` | `path`, `name`, `tag`, `layer`, `active`, `isStatic` |
| `gameobject/set-parent` | `path`, `parentPath`, `worldPositionStays` |
| `gameobject/duplicate` | `path`, `newName` |
| `component/add` | `gameObjectPath`, `typeName` |
| `component/remove` | `gameObjectPath`, `typeName`, `index` |
| `component/get` | `gameObjectPath`, `typeName`, `index` |
| `component/modify` | `gameObjectPath`, `typeName`, `fields` |
| `transform/get` | `path`, `instanceId` |
| `transform/set` | `path`, `position`, `rotation`, `scale`, `local` |
| `scene/hierarchy` | `depth`, `includeComponents` |
| `prefab/create` | `gameObjectPath`, `savePath` |
| `prefab/instantiate` | `assetPath`, `parentPath`, `position` |
| `prefab/unpack` | `gameObjectPath`, `full` |
| `material/create` | `savePath`, `shaderName` |
| `material/get` | `assetPath`, `gameObjectPath` |
| `material/assign` | `gameObjectPath`, `materialPath`, `index` |
| `screenshot/scene-view` | `savePath`, `width`, `height` |
| `screenshot/game-view` | `savePath`, `width`, `height`, `superSize` |
| `profiler/start` | `deep`, `logFile` |
| `profiler/stop` | — |
| `profiler/status` | — |
| `profiler/save` | `savePath` |
| `editor/status` | — |
| `editor/playmode.status` | — |
| `editor/playmode.enter` | — |
| `editor/playmode.exit` | — |
| `editor/menu.open` | `menuPath` |
| `editor/window.open` | `typeName`, `utility` |
| `editor/console.get` | — |
| `editor/console.clear` | — |
| `project/scene.list` | — |
| `project/scene.open` | `scenePath`, `mode` |
| `project/scene.save` | `scenePath`, `saveAsCopy` |
| `project/selection.get` | — |
| `project/selection.set` | `instanceIds`, `assetPaths` |
| `project/asset.list` | `filter`, `folders` |
| `project/asset.import` | `assetPath`, `forceSynchronousImport` |
| `project/asset.reimport` | `assetPath`, `forceSynchronousImport` |
| `session/list` | — |
| `session/inspect` | — |
| `session/reset` | — |
| `command/list` | — |

</details>

### Custom Commands

Add `[CommandAction]` to any static method — auto-discovered at startup, no registration needed:

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    [CommandAction("custom", "greet", summary: "Say hello")]
    private static CommandResponse Greet(CommandActionContext context)
    {
        var name = context.Request.GetArg("name", "World");
        return context.Ok($"Hello, {name}!", "{}");
    }
}
```

Run `/unity-cli-refresh-commands` to make Claude aware of new commands.

### Architecture

```
Claude Code                      Unity Editor
┌──────────────────┐            ┌──────────────────────────┐
│  Skills          │            │  com.zh1zh1.csharpconsole │
│  ┌────────────┐  │            │  ┌────────────────────┐  │
│  │ cli-command │──┼── HTTP ──▶│  │ ConsoleHttpService  │  │
│  │ cli-exec   │  │            │  │  ├─ CommandRouter   │  │
│  └────────────┘  │            │  │  ├─ REPL Compiler   │  │
│                  │            │  │  └─ REPL Executor   │  │
│  Python CLI      │            │  └────────────────────┘  │
│  ┌────────────┐  │            │                          │
│  │ cs.py      │  │            │  40+ CommandActions       │
│  │ core_bridge│  │            │  (GameObject, Component,  │
│  └────────────┘  │            │   Prefab, Material, ...)  │
└──────────────────┘            └──────────────────────────┘
```

- **Plugin layer**: Skills and slash commands invoked by Claude Code
- **CLI layer**: Python dispatcher, serializes requests to JSON
- **Unity layer**: [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP service, auto-discovered command handlers, Roslyn C# REPL

Auto-detects project root and service port. No manual configuration.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `service: UNREACHABLE` | Make sure Unity Editor is open with the project loaded |
| `package: NOT FOUND` | Run `/unity-cli-setup` or check `Packages/manifest.json` |
| Port conflict | Service auto-advances to the next free port. Check `Temp/CSharpConsole/refresh_state.json` |
| Commands not found | Ensure the package compiled successfully (no errors in Unity Console) |

---

## License

[Apache-2.0](LICENSE)

---

If this plugin saves you time, consider giving it a star. It helps others find it.
