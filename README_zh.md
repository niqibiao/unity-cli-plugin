# unity-cli-plugin

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Unity 2022.3+](https://img.shields.io/badge/Unity-2022.3%2B-blue.svg)](https://unity.com/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet.svg)](https://claude.ai/code)

[English](README.md) | 中文

> **依赖 [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)** — 基于 Roslyn 的 Unity 交互式 C# REPL，支持跨提交状态保持、私有成员访问、语义补全、远程运行时执行（通过 HybridCLR 支持 IL2CPP）和可扩展命令框架。

---

一个 [Claude Code](https://claude.ai/code) 的 Unity Editor 插件 —— 40+ 命令覆盖场景编辑、组件、资产、截图、性能分析等。基于 [**unity-csharpconsole**](https://github.com/niqibiao/unity-csharpconsole)。

```
你：     "创建 10 个 Cube 围成一圈，每个加上 Rigidbody"
Claude:  完成。10 个 Cube 已在半径 5 处创建，均已添加 Rigidbody 组件。
```

### 为什么用 CLI + Skill，而不是 MCP？

与 [Playwright CLI](https://github.com/microsoft/playwright-cli) 相同的架构 —— 通过 Claude Code 的 Skill 体系暴露 CLI 命令，而非 MCP。原因：

- **省 token。** Skill 按需加载；MCP 每次请求都加载全部工具 Schema。
- **无限制。** 可回退到完整的 [Roslyn C# REPL](https://github.com/niqibiao/unity-csharpconsole) —— 不受预定义工具限制。
- **无需额外进程。** 服务运行在 Unity Editor 进程内，零额外基础设施。
- **感知工作流。** 理解 Unity 的编译生命周期、Play Mode、域重载。

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
claude plugin install github:niqibiao/unity-cli-plugin

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

如果这个插件对你有帮助，请给个 Star，让更多人发现它。
