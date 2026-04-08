<div align="center">

# unity-cli-plugin

**Claude Code plugin for Unity Editor — powered by [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Unity](https://img.shields.io/badge/Unity-2022.3%2B-black.svg?logo=unity)](https://unity.com/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-blueviolet.svg?logo=anthropic)](https://claude.ai/code)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-00A67E.svg?logo=openai)](https://github.com/niqibiao/unity-cli-plugin/tree/codex-plugin)

40+ commands for scene editing, components, assets, screenshots, profiling, and more.<br/>
Depends on **[unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)** — a Roslyn-powered interactive C# REPL for Unity.

[Quick Start](#quick-start) · [Usage](#usage) · [Commands](#commands) · [Custom Commands](#custom-commands) · [Architecture](#architecture)

English | [中文](README_zh.md)

</div>

---

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


|                          | CLI + Skills (this plugin) | MCP                  |
| ------------------------ | -------------------------- | -------------------- |
| Context window cost      | **Low** (on-demand)        | High (always loaded) |
| C# REPL fallback         | **Yes**                    | Limited or none      |
| External server          | **None** (in-process)      | Required             |
| Play-mode-aware refresh  | **Yes**                    | No                   |
| Custom command discovery | **Automatic**              | Manual registration  |
| Runtime / IL2CPP         | **Yes** (HybridCLR)        | Varies               |


### Quick Start

**Prerequisites:** [Claude Code](https://claude.ai/code), Unity 2022.3+, Python 3.7+

```bash
# 1. Add the marketplace & install the plugin
claude plugin marketplace add niqibiao/unity-cli-plugin
claude plugin install unity-cli-plugin

# 2. Install the Unity package (inside your project)
claude
> /unity-cli-setup

# 3. Verify
> /unity-cli-status
```

#### Codex CLI Support

This plugin also supports [Codex CLI](https://github.com/openai/codex). Use the `codex-plugin` branch:

```bash
# 1. Install the plugin from the codex-plugin branch
$plugin-creator install https://github.com/niqibiao/unity-cli-plugin/tree/codex-plugin

# 2. Find and install the plugin
/plugins  # locate unity-cli-plugin, then run install

# 3. Restart Codex and initialize
$unity-cli-plugin:unity-cli-setup
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


| Command                       | Description                                  |
| ----------------------------- | -------------------------------------------- |
| `/unity-cli-setup`            | Install the Unity package                    |
| `/unity-cli-status`           | Check package and service status             |
| `/unity-cli-refresh`          | Trigger asset refresh / recompile            |
| `/unity-cli-refresh-commands` | Refresh cached custom command list           |
| `/unity-cli-sync-catalog`     | Compare local command catalog with live list |


#### Direct CLI

```bash
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'
python cli/cs.py refresh --json --project . --exit-playmode --wait 60
python cli/cs.py batch --json --project . '[{"ns":"gameobject","action":"create","args":{"name":"A"}},{"ns":"gameobject","action":"create","args":{"name":"B"}}]'
python cli/cs.py list-commands --json --project . --timeout 10
```

### Commands

46 built-in commands across 12 namespaces. All commands support `--json` output.

#### gameobject


| Action       | Description                                           |
| ------------ | ----------------------------------------------------- |
| `find`       | Find GameObjects by name, tag, or component type      |
| `create`     | Create a new GameObject (empty or primitive)          |
| `destroy`    | Destroy a GameObject                                  |
| `get`        | Get detailed info about a GameObject                  |
| `modify`     | Change name, tag, layer, active state, or static flag |
| `set_parent` | Reparent a GameObject                                 |
| `duplicate`  | Duplicate a GameObject                                |


#### component


| Action   | Description                              |
| -------- | ---------------------------------------- |
| `add`    | Add a component to a GameObject          |
| `remove` | Remove a component from a GameObject     |
| `get`    | Get serialized field data of a component |
| `modify` | Modify serialized fields of a component  |


#### transform


| Action | Description                                           |
| ------ | ----------------------------------------------------- |
| `get`  | Get position, rotation, and scale                     |
| `set`  | Set position, rotation, and/or scale (local or world) |


#### scene


| Action      | Description                                                       |
| ----------- | ----------------------------------------------------------------- |
| `hierarchy` | Get the full scene hierarchy tree, optionally with component info |


#### prefab


| Action        | Description                                   |
| ------------- | --------------------------------------------- |
| `create`      | Create a prefab asset from a scene GameObject |
| `instantiate` | Instantiate a prefab into the active scene    |
| `unpack`      | Unpack a prefab instance                      |


#### material


| Action   | Description                                         |
| -------- | --------------------------------------------------- |
| `create` | Create a new material asset with a specified shader |
| `get`    | Get material properties from an asset or a Renderer |
| `assign` | Assign a material to a Renderer component           |


#### screenshot


| Action       | Description                             |
| ------------ | --------------------------------------- |
| `scene_view` | Capture the Scene View to an image file |
| `game_view`  | Capture the Game View to an image file  |


#### profiler


| Action   | Description                                        |
| -------- | -------------------------------------------------- |
| `start`  | Start Profiler recording (optional deep profiling) |
| `stop`   | Stop Profiler recording                            |
| `status` | Get current Profiler state                         |
| `save`   | Save recorded profiler data to a `.raw` file       |


#### editor


| Action            | Description                         |
| ----------------- | ----------------------------------- |
| `status`          | Get editor state and play mode info |
| `playmode.status` | Get current play mode state         |
| `playmode.enter`  | Enter play mode                     |
| `playmode.exit`   | Exit play mode                      |
| `menu.open`       | Execute a menu item by path         |
| `window.open`     | Open an editor window by type name  |
| `console.get`     | Get editor console log entries      |
| `console.clear`   | Clear the editor console            |


#### project


| Action           | Description                      |
| ---------------- | -------------------------------- |
| `scene.list`     | List all scenes in the project   |
| `scene.open`     | Open a scene by path             |
| `scene.save`     | Save the current scene           |
| `selection.get`  | Get the current editor selection |
| `selection.set`  | Set the editor selection         |
| `asset.list`     | List assets by type filter       |
| `asset.import`   | Import an asset by path          |
| `asset.reimport` | Reimport an asset by path        |


#### session


| Action    | Description                             |
| --------- | --------------------------------------- |
| `list`    | List active REPL sessions               |
| `inspect` | Inspect a session's state               |
| `reset`   | Reset a session's compiler and executor |


#### command


| Action | Description                                      |
| ------ | ------------------------------------------------ |
| `list` | List all registered commands (built-in + custom) |


### Custom Commands

Add `[CommandAction]` to any static method — auto-discovered at startup, no registration needed. Parameters are bound automatically from JSON args by name.

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    // Minimal form — return (bool, string) tuple
    [CommandAction("custom", "greet", summary: "Say hello")]
    private static (bool, string) Greet(string name = "World")
    {
        return (true, $"Hello, {name}!");
    }
}
```

For structured data, return `CommandResponse`:

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    [CommandAction("mygame", "spawn", editorOnly: true, runOnMainThread: true, summary: "Spawn prefab instances")]
    private static CommandResponse Spawn(string prefabPath, int count = 1)
    {
        // ... instantiation logic ...
        return CommandResponseFactory.Ok($"Spawned {count} instance(s)");
    }
}
```

Run `/unity-cli-refresh-commands` to make Claude aware of new commands.

### Architecture

```
Claude Code                      Unity Editor
┌──────────────────┐            ┌──────────────────────────┐
│  Skills          │            │  com.zh1zh1.csharpconsole│
│  ┌────────────┐  │            │  ┌────────────────────┐  │
│  │ cli-command│──┼── HTTP ──▶ │  │ ConsoleHttpService │  │
│  │ cli-exec   │  │            │  │  ├─ CommandRouter  │  │
│  └────────────┘  │            │  │  ├─ REPL Compiler  │  │
│                  │            │  │  └─ REPL Executor  │  │
│  Python CLI      │            │  └────────────────────┘  │
│  ┌────────────┐  │            │                          │
│  │ cs.py      │  │            │  40+ CommandActions      │
│  │ core_bridge│  │            │  (GameObject, Component, │
│  └────────────┘  │            │   Prefab, Material, ...) │
└──────────────────┘            └──────────────────────────┘
```

- **Plugin layer**: Skills and slash commands invoked by Claude Code
- **CLI layer**: Python dispatcher, serializes requests to JSON
- **Unity layer**: [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP service, auto-discovered command handlers, Roslyn C# REPL

Auto-detects project root and service port. No manual configuration.

### Troubleshooting


| Problem                | Solution                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| `service: UNREACHABLE` | Make sure Unity Editor is open with the project loaded                                     |
| `package: NOT FOUND`   | Run `/unity-cli-setup` or check `Packages/manifest.json`                                   |
| Port conflict          | Service auto-advances to the next free port. Check `Temp/CSharpConsole/refresh_state.json` |
| Commands not found     | Ensure the package compiled successfully (no errors in Unity Console)                      |
| Version mismatch       | Run `/unity-cli-status` to check version info. Update the package if protocol differs      |


---

## License

[Apache-2.0](LICENSE)

---

If this plugin saves you time, consider giving it a star. It helps others find it.