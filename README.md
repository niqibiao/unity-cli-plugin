# unity-cli-plugin

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Unity 2022.3+](https://img.shields.io/badge/Unity-2022.3%2B-blue.svg)](https://unity.com/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet.svg)](https://claude.ai/code)

[English](#english) | [中文](#中文)

> **Depends on [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)** — A Roslyn-powered interactive C# REPL for Unity with cross-submission state, private member access, semantic completion, remote runtime execution (IL2CPP via HybridCLR), and an extensible command framework.

---

<a id="english"></a>

## English

A [Claude Code](https://claude.ai/code) plugin for Unity Editor — 40+ commands for scene editing, components, assets, screenshots, profiling, and more. Powered by [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole).

```
You:    "Create 10 cubes in a circle and add Rigidbody to each"
Claude: Done. 10 cubes created at radius 5, each with a Rigidbody component.
```

### CLI + Skills, Not MCP

> *"Modern coding agents increasingly favor CLI-based workflows exposed as skills over MCP because CLI invocations are more token-efficient: they avoid loading large tool schemas into the model context."* — [Playwright CLI](https://github.com/microsoft/playwright-cli)

This plugin follows the same approach Microsoft chose for [Playwright CLI](https://github.com/microsoft/playwright-cli) — **CLI commands exposed through Claude Code's skill system** instead of MCP tool-calling. The key differences:

- **Token-efficient.** MCP loads all 40+ tool JSON schemas into the context window on every request. Skills load only when triggered, only the relevant context.
- **Unrestricted.** MCP integrations are limited to predefined tools. This plugin falls back to a full [Roslyn C# REPL](https://github.com/niqibiao/unity-csharpconsole) with cross-submission state, private member access, and LINQ over live scene objects.
- **No sidecar process.** MCP needs a separate server. This plugin's service runs inside the Unity Editor process — zero extra infrastructure.
- **Workflow-aware.** The plugin understands Unity's compilation lifecycle — checks `ScriptCompilationDuringPlay`, exits play mode if needed, waits for domain reload. MCP tools have no concept of this.

MCP remains relevant for generic multi-LLM setups where broad compatibility matters more than token efficiency. For Claude Code + Unity, CLI + Skills is the better fit.

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
claude install-plugin github:niqibiao/unity-cli-plugin

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

<a id="中文"></a>

## 中文

一个 [Claude Code](https://claude.ai/code) 的 Unity Editor 插件 —— 40+ 命令覆盖场景编辑、组件、资产、截图、性能分析等。基于 [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole)。

```
你：     "创建 10 个 Cube 围成一圈，每个加上 Rigidbody"
Claude:  完成。10 个 Cube 已在半径 5 处创建，均已添加 Rigidbody 组件。
```

### 为什么用 CLI + Skill，而不是 MCP？

> *"现代编程 Agent 越来越倾向于通过 Skill 暴露的 CLI 工作流，而非 MCP，因为 CLI 调用更省 token：它避免了将大量工具 Schema 加载到模型上下文中。"* — [Playwright CLI](https://github.com/microsoft/playwright-cli)

本插件采用与微软 [Playwright CLI](https://github.com/microsoft/playwright-cli) 相同的架构 —— **通过 Claude Code 的 Skill 体系暴露 CLI 命令**，而非 MCP 工具调用。核心区别：

- **省 token。** MCP 每次请求都加载全部 40+ 工具的 JSON Schema 到上下文窗口。Skill 仅在触发时加载，且只加载相关上下文。
- **无限制。** MCP 集成受限于预定义工具。本插件可回退到完整的 [Roslyn C# REPL](https://github.com/niqibiao/unity-csharpconsole)，支持跨提交状态保持、私有成员访问、LINQ 查询场景对象。
- **无需额外进程。** MCP 需要独立服务进程。本插件的服务运行在 Unity Editor 进程内部 —— 零额外基础设施。
- **感知工作流。** 插件理解 Unity 的编译生命周期 —— 检查 `ScriptCompilationDuringPlay`，必要时退出 Play Mode，等待域重载。MCP 工具没有这种概念。

MCP 适合需要广泛 LLM 兼容性的通用场景。对于 Claude Code + Unity，CLI + Skill 是更好的选择。

| | CLI + Skill（本插件） | MCP |
|-|:---------------------:|:---:|
| 上下文窗口消耗 | **低**（按需加载） | 高（始终加载） |
| C# REPL 兜底 | **支持** | 有限或无 |
| 外部服务器 | **无**（进程内） | 需要 |
| 感知 Play Mode 的刷新 | **支持** | 否 |
| 自定义命令发现 | **自动** | 手动注册 |
| 运行时 / IL2CPP | **支持**（HybridCLR） | 视情况 |

### 快速开始

**前置条件：** [Claude Code](https://claude.ai/code)、Unity 2022.3+、Python 3.7+

```bash
# 1. 安装插件
claude install-plugin github:niqibiao/unity-cli-plugin

# 2. 安装 Unity 包（在项目目录下）
claude
> /unity-cli-setup

# 3. 验证
> /unity-cli-status
```

### 使用方式

直接告诉 Claude 你想做什么：

```
> 在场景里添加一个方向光，X 轴旋转 45 度
> 找出所有标签为 "Enemy" 的对象，列出它们的组件
> 截取 Scene View 的截图
> 开始 Profiler 录制，启用深度分析
```

Claude 会自动选择合适的命令，或在需要时编写 C# 代码。

#### 斜杠命令

| 命令 | 说明 |
|------|------|
| `/unity-cli-setup` | 安装 Unity 包 |
| `/unity-cli-status` | 检查包和服务状态 |
| `/unity-cli-refresh` | 触发资产刷新 / 重编译 |
| `/unity-cli-refresh-commands` | 刷新缓存的自定义命令列表 |

#### 直接使用 CLI

```bash
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'
python cli/cs.py refresh --json --project . --wait 60
python cli/cs.py list-commands --json --project .
```

### 命令

12 个命名空间、46 个命令。所有命令支持 `--json` 输出。

**gameobject** — `find`, `create`, `destroy`, `get`, `modify`, `set-parent`, `duplicate`

**component** — `add`, `remove`, `get`, `modify`

**transform** — `get`, `set`（位置/旋转/缩放，本地或世界坐标）

**scene** — `hierarchy`（完整层级树，可选组件信息）

**prefab** — `create`, `instantiate`, `unpack`

**material** — `create`, `get`, `assign`

**screenshot** — `scene-view`, `game-view`

**profiler** — `start`, `stop`, `status`, `save`

**editor** — `status`, `playmode.status`, `playmode.enter`, `playmode.exit`, `menu.open`, `window.open`, `console.get`, `console.clear`

**project** — `scene.list`, `scene.open`, `scene.save`, `selection.get`, `selection.set`, `asset.list`, `asset.import`, `asset.reimport`

**session** — `list`, `inspect`, `reset`

**command** — `list`

<details>
<summary>完整命令参数参考</summary>

| 命令 | 参数 |
|------|------|
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

### 自定义命令

给任意静态方法加上 `[CommandAction]` —— 启动时自动发现，无需注册：

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

运行 `/unity-cli-refresh-commands` 让 Claude 感知新命令。

### 架构

```
Claude Code                      Unity Editor
┌──────────────────┐            ┌──────────────────────────┐
│  Skills          │            │  com.zh1zh1.csharpconsole │
│  ┌────────────┐  │            │  ┌────────────────────┐  │
│  │ cli-command │──┼── HTTP ──▶│  │ ConsoleHttpService  │  │
│  │ cli-exec   │  │            │  │  ├─ CommandRouter   │  │
│  └────────────┘  │            │  │  ├─ REPL 编译器     │  │
│                  │            │  │  └─ REPL 执行器     │  │
│  Python CLI      │            │  └────────────────────┘  │
│  ┌────────────┐  │            │                          │
│  │ cs.py      │  │            │  40+ CommandActions       │
│  │ core_bridge│  │            │  (GameObject, Component,  │
│  └────────────┘  │            │   Prefab, Material, ...)  │
└──────────────────┘            └──────────────────────────┘
```

- **插件层**：Claude Code 调用的 Skills 和斜杠命令
- **CLI 层**：Python 调度器，将请求序列化为 JSON
- **Unity 层**：[unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP 服务，自动发现命令处理器，Roslyn C# REPL

自动检测项目根目录和服务端口，无需手动配置。

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `service: UNREACHABLE` | 确保 Unity 编辑器已打开并加载了项目 |
| `package: NOT FOUND` | 运行 `/unity-cli-setup` 或检查 `Packages/manifest.json` |
| 端口冲突 | 服务会自动切换到下一个可用端口，查看 `Temp/CSharpConsole/refresh_state.json` |
| 找不到命令 | 确保包编译成功（Unity Console 中无报错） |

---

## License

[Apache-2.0](LICENSE)

---

If this plugin saves you time, consider giving it a star. It helps others find it.

如果这个插件对你有帮助，请给个 Star，让更多人发现它。
