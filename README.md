# Claude Code Unity

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Unity 2022.3+](https://img.shields.io/badge/Unity-2022.3%2B-blue.svg)](https://unity.com/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet.svg)](https://claude.ai/code)

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

A [Claude Code](https://claude.ai/code) plugin that gives Claude direct access to your Unity Editor — create GameObjects, edit scenes, manage assets, capture screenshots, profile performance, and more, all through natural language.

Powered by [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole) — an interactive C# REPL and remote execution package for Unity, with Roslyn compilation, cross-submission state, and a command framework.

```
You:    "Create 10 cubes in a circle and add Rigidbody to each"
Claude: Done. 10 cubes created at radius 5, each with a Rigidbody component.
```

### What Can It Do?

| Category | Examples |
|----------|---------|
| **Scene Editing** | Create/delete/duplicate GameObjects, set parent, modify properties |
| **Components** | Add Rigidbody, get serialized fields, modify any component property |
| **Transform** | Set position/rotation/scale in local or world space |
| **Prefabs** | Create prefab from scene object, instantiate, unpack |
| **Materials** | Create materials, assign shaders, apply to renderers |
| **Assets** | List, import, reimport project assets |
| **Scenes** | Open, save, list scenes, get full hierarchy tree |
| **Screenshots** | Capture Scene View and Game View |
| **Profiler** | Start/stop recording, deep profiling, save .raw data |
| **Console** | Read and clear Unity Editor console logs |
| **Play Mode** | Enter/exit play mode, check editor status |
| **Asset Refresh** | Trigger recompilation after editing C# files, with play-mode-aware safety |
| **C# REPL** | Execute arbitrary C# code as a fallback for anything else |

**40+ built-in commands** with full undo support. If a command doesn't exist, Claude falls back to raw C# execution — so nothing is out of reach.

### Quick Start

#### Prerequisites

- [Claude Code](https://claude.ai/code) (CLI, Desktop App, or IDE extension)
- Unity 2022.3 or later
- Python 3.7+

#### 1. Install the plugin

```bash
claude install-plugin github:niqibiao/unity-cli-plugin
```

#### 2. Install the Unity package

Open a terminal in your Unity project, then:

```bash
claude
> /unity-cli-setup
```

Choose **git** (recommended) or **local** (for development). Wait for Unity to resolve the package.

#### 3. Verify connection

```bash
> /unity-cli-status
```

```
project: /path/to/your/unity/project
package: OK
service: OK
```

You're ready to go. Start talking to Claude about your Unity project.

### Usage

#### Natural Language (Recommended)

Just tell Claude what you want:

```
> Add a directional light to the scene and rotate it 45 degrees on X

> Find all objects tagged "Enemy" and list their components

> Take a screenshot of the Scene View and save it to Assets/Screenshots/

> Start profiler recording with deep profiling enabled
```

Claude automatically picks the right command or writes C# code as needed.

#### Slash Commands

| Command | Description |
|---------|-------------|
| `/unity-cli-setup` | Install the Unity package into your project |
| `/unity-cli-status` | Check package installation and service connectivity |
| `/unity-cli-refresh` | Trigger asset refresh and wait for script compilation |
| `/unity-cli-refresh-commands` | Refresh cached custom command list from Unity |

#### Direct CLI Usage

The plugin includes a Python CLI that can be used independently:

```bash
# Execute C# code
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"

# Run a framework command
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'

# Trigger asset refresh and wait for compilation
python cli/cs.py refresh --json --project . --wait 60

# List all available commands
python cli/cs.py list-commands --json --project .
```

### Command Reference

<details>
<summary><b>gameobject</b> — Scene object manipulation (7 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `gameobject/find` | Find objects by name, tag, or component type | `name`, `tag`, `componentType` |
| `gameobject/create` | Create empty or primitive object | `name`, `primitiveType`, `parentPath` |
| `gameobject/destroy` | Delete an object | `path`, `instanceId` |
| `gameobject/get` | Get detailed info (transform, components) | `path`, `instanceId` |
| `gameobject/modify` | Change name, tag, layer, active, static | `path`, `name`, `tag`, `layer` |
| `gameobject/set-parent` | Reparent an object | `path`, `parentPath` |
| `gameobject/duplicate` | Duplicate an object | `path`, `newName` |

</details>

<details>
<summary><b>component</b> — Component operations (4 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `component/add` | Add a component | `gameObjectPath`, `typeName` |
| `component/remove` | Remove a component | `gameObjectPath`, `typeName`, `index` |
| `component/get` | Get serialized field data | `gameObjectPath`, `typeName` |
| `component/modify` | Modify component fields | `gameObjectPath`, `typeName`, `fieldsJson` |

</details>

<details>
<summary><b>transform</b> — Position, rotation, scale (2 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `transform/get` | Get transform values | `path` |
| `transform/set` | Set position/rotation/scale | `path`, `position`, `rotation`, `scale`, `local` |

</details>

<details>
<summary><b>scene</b> — Scene hierarchy (1 command)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `scene/hierarchy` | Get full scene tree | `depth`, `includeComponents` |

</details>

<details>
<summary><b>prefab</b> — Prefab workflow (3 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `prefab/create` | Create prefab from scene object | `gameObjectPath`, `savePath` |
| `prefab/instantiate` | Instantiate prefab into scene | `assetPath`, `parentPath`, `position` |
| `prefab/unpack` | Unpack prefab instance | `gameObjectPath`, `full` |

</details>

<details>
<summary><b>material</b> — Material management (3 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `material/create` | Create a new material | `savePath`, `shaderName` |
| `material/get` | Get material properties | `assetPath` |
| `material/assign` | Assign material to renderer | `gameObjectPath`, `materialPath`, `index` |

</details>

<details>
<summary><b>screenshot</b> — View capture (2 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `screenshot/scene-view` | Capture Scene View | `savePath`, `width`, `height` |
| `screenshot/game-view` | Capture Game View | `savePath`, `superSize` |

</details>

<details>
<summary><b>profiler</b> — Performance recording (4 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `profiler/start` | Start recording | `deep`, `logFile` |
| `profiler/stop` | Stop recording | — |
| `profiler/status` | Get profiler state | — |
| `profiler/save` | Save data to .raw file | `savePath` |

</details>

<details>
<summary><b>editor</b> — Editor control (8 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `editor/status` | Get editor state and play mode info | — |
| `editor/playmode.status` | Get current play mode state | — |
| `editor/playmode.enter` | Enter play mode | — |
| `editor/playmode.exit` | Exit play mode | — |
| `editor/menu.open` | Open a menu item by path | `menuPath` |
| `editor/window.open` | Open an editor window by type name | `typeName`, `utility` |
| `editor/console.get` | Get editor console log entries | — |
| `editor/console.clear` | Clear the editor console | — |

</details>

<details>
<summary><b>project</b> — Asset and scene management (8 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `project/scene.list` | List all scenes in the project | — |
| `project/scene.open` | Open a scene by path (single/additive) | `scenePath`, `mode` |
| `project/scene.save` | Save the current scene | `scenePath`, `saveAsCopy` |
| `project/selection.get` | Get the current editor selection | — |
| `project/selection.set` | Set the editor selection by name or path | `instanceIds`, `assetPaths` |
| `project/asset.list` | List assets by type filter | `filter`, `folders` |
| `project/asset.import` | Import an asset by path | `assetPath`, `forceSynchronousImport` |
| `project/asset.reimport` | Reimport an asset by path | `assetPath`, `forceSynchronousImport` |

</details>

<details>
<summary><b>session</b> — REPL session management (3 commands)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `session/list` | List active REPL sessions | — |
| `session/inspect` | Inspect a session's state | — |
| `session/reset` | Reset a session's compiler and executor | — |

</details>

<details>
<summary><b>command</b> — Introspection (1 command)</summary>

| Command | Description | Key Args |
|---------|-------------|----------|
| `command/list` | List all registered commands | — |

</details>

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

- **Plugin layer**: Skills and slash commands that Claude Code invokes
- **CLI layer**: Python dispatcher that serializes requests to JSON
- **Unity layer**: [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP service with auto-discovered command handlers, Roslyn-based C# REPL

The CLI auto-detects the Unity project root and service port. No manual configuration needed.

### Why CLI + Skills, Not MCP?

> *"Modern coding agents increasingly favor CLI-based workflows exposed as skills over MCP because CLI invocations are more token-efficient: they avoid loading large tool schemas into the model context, allowing agents to act through concise, purpose-built commands."* — [Playwright CLI](https://github.com/microsoft/playwright-cli)

MCP-based Unity integrations (unity-mcp, Unity-MCP, etc.) work through a generic tool-calling protocol. Every MCP tool's JSON schema is loaded into the context window on every request — for a Unity integration with 40+ commands, that alone costs thousands of tokens before Claude even starts thinking. This plugin takes a different approach:

**Token-efficient CLI over schema-heavy MCP.** This plugin exposes Unity operations as CLI commands invoked through Claude Code's skill system. Skills load only when triggered and only the relevant context — no 40-tool JSON schema bloat on every turn. This is the same architecture Microsoft chose for [Playwright CLI](https://github.com/microsoft/playwright-cli) over their own MCP server, for the same reason: *better suited for agents that must balance tool automation with large codebases within limited context windows.*

**C# REPL as an escape hatch, not a limitation.** Most MCP integrations are limited to the tools they define — if there is no "set skybox" tool, you are stuck. This plugin falls back to a full Roslyn REPL with cross-submission state, private member access, and LINQ over live scene objects. Nothing is out of reach.

**No sidecar process.** MCP requires a separate server process (Python, Node, or binary) running alongside Unity. This plugin's HTTP service runs inside the Unity Editor process itself — no extra terminal, no port forwarding, no process to manage.

**Play-mode-aware workflows.** The plugin understands Unity's compilation lifecycle. When you edit C# files, it checks `ScriptCompilationDuringPlay` preference, asks whether to exit play mode if needed, triggers `AssetDatabase.Refresh`, and waits for domain reload to complete — all automatically. MCP tools have no concept of this.

**Custom commands with zero boilerplate.** Add `[CommandAction]` to any static method in your project and the plugin discovers it at startup. No server restart, no tool-schema registration, no JSON schema authoring.

| Feature | This Plugin (CLI + Skills) | MCP-based Integrations |
|---------|:--------------------------:|:----------------------:|
| Context window cost | **Low** (skills load on demand) | High (all tool schemas always loaded) |
| Claude Code native skills | **Yes** | No (generic tool protocol) |
| C# REPL fallback | **Yes** (Roslyn, cross-submission state) | Limited or none |
| No external server | **Yes** (runs in-process) | Requires sidecar process |
| Zero config | **Yes** (auto-detect project + port) | Manual setup |
| Play-mode-aware refresh | **Yes** | No |
| Custom command discovery | **Yes** (attribute-based) | Manual tool registration |
| Works in Runtime (IL2CPP) | **Yes** (via HybridCLR) | Varies |

### Adding Custom Commands

Create a new C# class in your Unity project with `[CommandAction]` attributes:

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    [Serializable]
    private sealed class GreetArgs { public string name = ""; }

    [CommandAction("custom", "greet", argsType: typeof(GreetArgs),
                   summary: "Say hello")]
    private static CommandResponse Greet(CommandActionContext context)
    {
        if (!context.TryParseArgs(out GreetArgs args))
            return context.ValidationError("Invalid args");

        return context.Ok($"Hello, {args.name}!", "{}");
    }
}
```

Commands are auto-discovered at startup. No registration code needed.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `service: UNREACHABLE` | Make sure Unity Editor is open with the project loaded |
| `package: NOT FOUND` | Run `/unity-cli-setup` or check `Packages/manifest.json` |
| Port conflict | The service auto-advances to the next free port. Check `Temp/CSharpConsole/refresh_state.json` |
| Commands not found | Ensure the package compiled successfully (no errors in Unity Console) |

---

<a id="中文"></a>

## 中文

一个 [Claude Code](https://claude.ai/code) 插件，让 Claude 直接操控你的 Unity 编辑器 —— 创建 GameObject、编辑场景、管理资产、截图、性能分析，全部通过自然语言完成。

基于 [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole) —— 一个 Unity 交互式 C# REPL 和远程执行包，支持 Roslyn 编译、跨提交状态保持和命令框架。

```
你：     "创建 10 个 Cube 围成一圈，每个加上 Rigidbody"
Claude:  完成。10 个 Cube 已在半径 5 处创建，均已添加 Rigidbody 组件。
```

### 功能一览

| 类别 | 示例 |
|------|------|
| **场景编辑** | 创建/删除/复制 GameObject，设置父节点，修改属性 |
| **组件操作** | 添加 Rigidbody，获取序列化字段，修改任意组件属性 |
| **Transform** | 设置位置/旋转/缩放（本地或世界坐标） |
| **预制体** | 从场景对象创建预制体，实例化，解包 |
| **材质** | 创建材质，分配 Shader，应用到渲染器 |
| **资产管理** | 列出、导入、重新导入项目资产 |
| **场景管理** | 打开、保存、列出场景，获取完整 Hierarchy 树 |
| **截图** | 截取 Scene View 和 Game View |
| **性能分析** | 开始/停止 Profiler 录制，深度分析，保存 .raw 数据 |
| **控制台** | 读取和清空 Unity 编辑器控制台日志 |
| **播放模式** | 进入/退出 Play Mode，检查编辑器状态 |
| **资产刷新** | 编辑 C# 文件后触发重编译，自动感知 Play Mode 安全设置 |
| **C# REPL** | 执行任意 C# 代码作为兜底方案 |

**40+ 内置命令**，全部支持 Undo。如果命令不存在，Claude 会自动回退到原始 C# 代码执行 —— 没有做不到的事。

### 快速开始

#### 前置条件

- [Claude Code](https://claude.ai/code)（CLI、桌面应用或 IDE 扩展均可）
- Unity 2022.3 或更高版本
- Python 3.7+

#### 1. 安装插件

```bash
claude install-plugin github:niqibiao/unity-cli-plugin
```

#### 2. 安装 Unity 包

在你的 Unity 项目目录下打开终端：

```bash
claude
> /unity-cli-setup
```

选择 **git**（推荐）或 **local**（适合开发调试）。等待 Unity 解析包。

#### 3. 验证连接

```bash
> /unity-cli-status
```

```
project: /path/to/your/unity/project
package: OK
service: OK
```

一切就绪，开始用自然语言操控你的 Unity 项目吧。

### 使用方式

#### 自然语言（推荐）

直接告诉 Claude 你想做什么：

```
> 在场景里添加一个方向光，X 轴旋转 45 度

> 找出所有标签为 "Enemy" 的对象，列出它们的组件

> 截取 Scene View 的截图，保存到 Assets/Screenshots/

> 开始 Profiler 录制，启用深度分析
```

Claude 会自动选择合适的命令，或在需要时编写 C# 代码。

#### 斜杠命令

| 命令 | 说明 |
|------|------|
| `/unity-cli-setup` | 将 Unity 包安装到项目中 |
| `/unity-cli-status` | 检查包安装状态和服务连接 |
| `/unity-cli-refresh` | 触发资产刷新并等待脚本编译 |
| `/unity-cli-refresh-commands` | 刷新缓存的自定义命令列表 |

#### 直接使用 CLI

插件附带的 Python CLI 可以独立使用：

```bash
# 执行 C# 代码
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"

# 运行框架命令
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'

# 触发资产刷新并等待编译
python cli/cs.py refresh --json --project . --wait 60

# 列出所有可用命令
python cli/cs.py list-commands --json --project .
```

### 命令参考

共 12 个命名空间、46 个命令：

<details>
<summary><b>gameobject</b> — 场景对象操作（7 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `gameobject/find` | 按名称、标签或组件类型查找对象 | `name`, `tag`, `componentType` |
| `gameobject/create` | 创建空对象或基本体 | `name`, `primitiveType`, `parentPath` |
| `gameobject/destroy` | 删除一个 GameObject | `path`, `instanceId` |
| `gameobject/get` | 获取 GameObject 详细信息（Transform、组件） | `path`, `instanceId` |
| `gameobject/modify` | 修改名称、标签、层、激活、静态等属性 | `path`, `name`, `tag`, `layer`, `active`, `isStatic` |
| `gameobject/set-parent` | 修改父节点 | `path`, `parentPath`, `worldPositionStays` |
| `gameobject/duplicate` | 复制一个 GameObject | `path`, `instanceId`, `newName` |

</details>

<details>
<summary><b>component</b> — 组件操作（4 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `component/add` | 添加组件到 GameObject | `gameObjectPath`, `typeName` |
| `component/remove` | 移除 GameObject 上的组件 | `gameObjectPath`, `typeName`, `index` |
| `component/get` | 获取组件的序列化字段数据 | `gameObjectPath`, `typeName`, `index` |
| `component/modify` | 修改组件的序列化字段 | `gameObjectPath`, `typeName`, `fields` |

</details>

<details>
<summary><b>transform</b> — 变换操作（2 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `transform/get` | 获取 Transform 值 | `path`, `instanceId` |
| `transform/set` | 设置位置/旋转/缩放 | `path`, `position`, `rotation`, `scale`, `local` |

</details>

<details>
<summary><b>scene</b> — 场景层级（1 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `scene/hierarchy` | 获取完整场景 Hierarchy 树 | `depth`, `includeComponents` |

</details>

<details>
<summary><b>prefab</b> — 预制体操作（3 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `prefab/create` | 从场景对象创建预制体 | `gameObjectPath`, `savePath` |
| `prefab/instantiate` | 实例化预制体到场景 | `assetPath`, `parentPath`, `position` |
| `prefab/unpack` | 解包预制体实例 | `gameObjectPath`, `full` |

</details>

<details>
<summary><b>material</b> — 材质操作（3 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `material/create` | 创建新材质 | `savePath`, `shaderName` |
| `material/get` | 获取材质属性 | `assetPath`, `gameObjectPath` |
| `material/assign` | 将材质分配给 Renderer | `gameObjectPath`, `materialPath`, `index` |

</details>

<details>
<summary><b>screenshot</b> — 截图（2 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `screenshot/scene-view` | 截取 Scene View | `savePath`, `width`, `height` |
| `screenshot/game-view` | 截取 Game View | `savePath`, `width`, `height`, `superSize` |

</details>

<details>
<summary><b>profiler</b> — 性能录制（4 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `profiler/start` | 开始 Profiler 录制 | `deep`, `logFile` |
| `profiler/stop` | 停止 Profiler 录制 | — |
| `profiler/status` | 获取 Profiler 当前状态 | — |
| `profiler/save` | 保存录制数据为 .raw 文件 | `savePath` |

</details>

<details>
<summary><b>editor</b> — 编辑器控制（8 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `editor/status` | 获取编辑器状态和 Play Mode 信息 | — |
| `editor/playmode.status` | 获取当前 Play Mode 状态 | — |
| `editor/playmode.enter` | 进入 Play Mode | — |
| `editor/playmode.exit` | 退出 Play Mode | — |
| `editor/menu.open` | 按路径打开菜单项 | `menuPath` |
| `editor/window.open` | 按类型名打开编辑器窗口 | `typeName`, `utility` |
| `editor/console.get` | 获取控制台日志条目 | — |
| `editor/console.clear` | 清空控制台 | — |

</details>

<details>
<summary><b>project</b> — 资产和场景管理（8 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `project/scene.list` | 列出项目中所有场景 | — |
| `project/scene.open` | 按路径打开场景（单场景/叠加） | `scenePath`, `mode` |
| `project/scene.save` | 保存当前场景 | `scenePath`, `saveAsCopy` |
| `project/selection.get` | 获取当前编辑器选中对象 | — |
| `project/selection.set` | 按名称或路径设置选中对象 | `instanceIds`, `assetPaths` |
| `project/asset.list` | 按类型筛选列出资产 | `filter`, `folders` |
| `project/asset.import` | 按路径导入资产 | `assetPath`, `forceSynchronousImport` |
| `project/asset.reimport` | 按路径重新导入资产 | `assetPath`, `forceSynchronousImport` |

</details>

<details>
<summary><b>session</b> — REPL 会话管理（3 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `session/list` | 列出活跃的 REPL 会话 | — |
| `session/inspect` | 检查会话状态 | — |
| `session/reset` | 重置会话的编译器和执行器 | — |

</details>

<details>
<summary><b>command</b> — 命令自省（1 个命令）</summary>

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `command/list` | 列出所有已注册命令 | — |

</details>

### 架构

```
Claude Code                      Unity 编辑器
┌──────────────────┐            ┌──────────────────────────┐
│  Skills 技能层    │            │  com.zh1zh1.csharpconsole │
│  ┌────────────┐  │            │  ┌────────────────────┐  │
│  │ cli-command │──┼── HTTP ──▶│  │ ConsoleHttpService  │  │
│  │ cli-exec   │  │            │  │  ├─ CommandRouter   │  │
│  └────────────┘  │            │  │  ├─ REPL 编译器     │  │
│                  │            │  │  └─ REPL 执行器     │  │
│  Python CLI 层   │            │  └────────────────────┘  │
│  ┌────────────┐  │            │                          │
│  │ cs.py      │  │            │  40+ CommandActions       │
│  │ core_bridge│  │            │  (GameObject, Component,  │
│  └────────────┘  │            │   Prefab, Material, ...)  │
└──────────────────┘            └──────────────────────────┘
```

- **插件层**：Claude Code 调用的 Skills 和斜杠命令
- **CLI 层**：Python 调度器，将请求序列化为 JSON
- **Unity 层**：[unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP 服务，自动发现的命令处理器，基于 Roslyn 的 C# REPL

CLI 自动检测 Unity 项目根目录和服务端口，无需手动配置。

### 为什么用 CLI + Skill，而不是 MCP？

> *"现代编程 Agent 越来越倾向于通过 Skill 暴露的 CLI 工作流，而非 MCP，因为 CLI 调用更省 token：它避免了将大量工具 Schema 加载到模型上下文中，让 Agent 通过简洁、专用的命令来行动。"* — [Playwright CLI](https://github.com/microsoft/playwright-cli)

基于 MCP 的 Unity 集成（unity-mcp、Unity-MCP 等）通过通用工具调用协议工作。每个 MCP 工具的 JSON Schema 在每次请求时都会被加载到上下文窗口 —— 一个有 40+ 命令的 Unity 集成，光 Schema 就要消耗数千 token，Claude 还没开始思考。本插件走了不同的路线：

**省 token 的 CLI，而非 Schema 臃肿的 MCP。** 本插件通过 Claude Code 的 Skill 体系将 Unity 操作暴露为 CLI 命令。Skill 仅在触发时加载，且只加载相关上下文 —— 不会每轮对话都塞入 40 个工具的 JSON Schema。这和微软为 [Playwright CLI](https://github.com/microsoft/playwright-cli) 选择 CLI 而非自家 MCP 服务的架构一致，理由相同：*更适合需要在有限上下文窗口内兼顾工具自动化和大型代码库的 Agent。*

**C# REPL 作为兜底，而非能力上限。** 大多数 MCP 集成受限于预定义的工具 —— 没有 "set skybox" 工具就束手无策。本插件可回退到完整的 Roslyn REPL，支持跨提交状态保持、私有成员访问、LINQ 查询场景对象。没有做不到的事。

**无需额外进程。** MCP 需要在 Unity 之外运行一个独立的服务进程（Python / Node / 二进制）。本插件的 HTTP 服务运行在 Unity Editor 进程内部 —— 不需要额外终端、不需要端口转发、不需要管理进程。

**感知 Play Mode 的工作流。** 编辑 C# 文件后，插件会检查 `ScriptCompilationDuringPlay` 偏好设置，必要时询问是否退出 Play Mode，触发 `AssetDatabase.Refresh` 并等待域重载完成 —— 全自动。MCP 工具没有这种概念。

**零样板代码的自定义命令。** 在项目中给任意静态方法加上 `[CommandAction]` 属性，插件启动时自动发现。无需重启服务、无需注册工具 Schema、无需编写 JSON Schema。

| 特性 | 本插件（CLI + Skill） | 基于 MCP 的集成 |
|------|:---------------------:|:---------------:|
| 上下文窗口消耗 | **低**（Skill 按需加载） | 高（所有工具 Schema 始终加载） |
| Claude Code 原生 Skill | **支持** | 否（通用工具协议） |
| C# REPL 兜底 | **支持**（Roslyn，跨提交状态） | 有限或无 |
| 无需外部服务器 | **是**（进程内运行） | 需要额外进程 |
| 零配置 | **是**（自动检测项目和端口） | 手动配置 |
| 感知 Play Mode 的刷新 | **支持** | 否 |
| 自定义命令发现 | **支持**（基于属性） | 手动注册工具 |
| 运行时可用（IL2CPP） | **是**（通过 HybridCLR） | 视情况而定 |

### 自定义命令

在 Unity 项目中创建带 `[CommandAction]` 属性的 C# 类即可：

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    [Serializable]
    private sealed class GreetArgs { public string name = ""; }

    [CommandAction("custom", "greet", argsType: typeof(GreetArgs),
                   summary: "Say hello")]
    private static CommandResponse Greet(CommandActionContext context)
    {
        if (!context.TryParseArgs(out GreetArgs args))
            return context.ValidationError("Invalid args");

        return context.Ok($"Hello, {args.name}!", "{}");
    }
}
```

命令在启动时自动发现，无需注册代码。

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
