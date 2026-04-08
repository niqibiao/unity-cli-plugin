<div align="center">

# unity-cli-plugin

**Unity Editor 的 Codex CLI 插件 — 基于 [unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Unity](https://img.shields.io/badge/Unity-2022.3%2B-black.svg?logo=unity)](https://unity.com/)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-blueviolet.svg?logo=openai)](https://codex.com)

40+ 命令覆盖场景编辑、组件、资产、截图、性能分析等。<br/>
依赖 **[unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole)** — 基于 Roslyn 的 Unity 交互式 C# REPL。

[快速开始](#快速开始) · [使用方式](#使用方式) · [命令](#命令) · [自定义命令](#自定义命令) · [架构](#架构)

[English](README.md) | 中文

</div>

---

```
你：     "创建 10 个 Cube 围成一圈，每个加上 Rigidbody"
Codex:  完成。10 个 Cube 已在半径 5 处创建，均已添加 Rigidbody 组件。
```

### 为什么用 CLI + Skill，而不是 MCP？

与 [Playwright CLI](https://github.com/microsoft/playwright-cli) 相同的架构 —— 通过 Codex CLI 的 Skill 体系暴露 CLI 命令，而非 MCP。原因：

- **省 token。** Skill 按需加载；MCP 每次请求都加载全部工具 Schema。
- **无限制。** 可回退到完整的 [Roslyn C# REPL](https://github.com/niqibiao/unity-csharpconsole) —— 不受预定义工具限制。
- **无需额外进程。** 服务运行在 Unity Editor 进程内，零额外基础设施。
- **感知工作流。** 理解 Unity 的编译生命周期、Play Mode、域重载。


|                  | CLI + Skill（本插件）  | MCP     |
| ---------------- | ----------------- | ------- |
| 上下文窗口消耗          | **低**（按需加载）       | 高（始终加载） |
| C# REPL 兜底       | **支持**            | 有限或无    |
| 外部服务器            | **无**（进程内）        | 需要      |
| 感知 Play Mode 的刷新 | **支持**            | 否       |
| 自定义命令发现          | **自动**            | 手动注册    |
| 运行时 / IL2CPP     | **支持**（HybridCLR） | 视情况     |


### 快速开始

**前置条件：** [Codex CLI](https://codex.com)、Unity 2022.3+、Python 3.7+

```bash
# 1. 添加市场源并安装插件
codex plugin install niqibiao/unity-cli-plugin
claude plugin install unity-cli-plugin

# 2. 安装 Unity 包（在项目目录下）
claude
> $unity-cli-setup

# 3. 验证
> $unity-cli-status
```

### 使用方式

直接告诉 Codex 你想做什么：

```
> 在场景里添加一个方向光，X 轴旋转 45 度
> 找出所有标签为 "Enemy" 的对象，列出它们的组件
> 截取 Scene View 的截图
> 开始 Profiler 录制，启用深度分析
```

Codex 会自动选择合适的命令，或在需要时编写 C# 代码。

#### 斜杠命令


| 命令                            | 说明              |
| ----------------------------- | --------------- |
| `$unity-cli-setup`            | 安装 Unity 包      |
| `$unity-cli-status`           | 检查包和服务状态        |
| `$unity-cli-refresh`          | 触发资产刷新 / 重编译    |
| `$unity-cli-refresh-commands` | 刷新缓存的自定义命令列表    |
| `$unity-cli-sync-catalog`     | 对比本地命令目录与实际命令列表 |


#### 直接使用 CLI

```bash
python cli/cs.py exec --json --project . "Debug.Log(\"Hello\")"
python cli/cs.py command --json --project . gameobject create '{"name":"Cube","primitiveType":"Cube"}'
python cli/cs.py refresh --json --project . --exit-playmode --wait 60
python cli/cs.py batch --json --project . '[{"ns":"gameobject","action":"create","args":{"name":"A"}},{"ns":"gameobject","action":"create","args":{"name":"B"}}]'
python cli/cs.py list-commands --json --project . --timeout 10
```

### 命令

12 个命名空间、46 个内置命令。所有命令支持 `--json` 输出。

#### gameobject


| Action       | 说明                       |
| ------------ | ------------------------ |
| `find`       | 按名称、标签或组件类型查找 GameObject |
| `create`     | 创建新 GameObject（空对象或基本体）  |
| `destroy`    | 销毁 GameObject            |
| `get`        | 获取 GameObject 详细信息       |
| `modify`     | 修改名称、标签、层、激活状态或静态标记      |
| `set_parent` | 设置父对象                    |
| `duplicate`  | 复制 GameObject            |


#### component


| Action   | 说明                |
| -------- | ----------------- |
| `add`    | 为 GameObject 添加组件 |
| `remove` | 移除组件              |
| `get`    | 获取组件的序列化字段数据      |
| `modify` | 修改组件的序列化字段        |


#### transform


| Action | 说明                    |
| ------ | --------------------- |
| `get`  | 获取位置、旋转和缩放            |
| `set`  | 设置位置、旋转和/或缩放（本地或世界坐标） |


#### scene


| Action      | 说明                 |
| ----------- | ------------------ |
| `hierarchy` | 获取完整场景层级树，可选包含组件信息 |


#### prefab


| Action        | 说明                            |
| ------------- | ----------------------------- |
| `create`      | 从场景中的 GameObject 创建 Prefab 资产 |
| `instantiate` | 将 Prefab 实例化到当前场景             |
| `unpack`      | 解包 Prefab 实例                  |


#### material


| Action   | 说明                 |
| -------- | ------------------ |
| `create` | 创建新材质（指定 Shader）   |
| `get`    | 获取材质属性             |
| `assign` | 将材质分配给 Renderer 组件 |


#### screenshot


| Action       | 说明                  |
| ------------ | ------------------- |
| `scene_view` | 截取 Scene View 到图片文件 |
| `game_view`  | 截取 Game View 到图片文件  |


#### profiler


| Action   | 说明                     |
| -------- | ---------------------- |
| `start`  | 开始 Profiler 录制（可选深度分析） |
| `stop`   | 停止 Profiler 录制         |
| `status` | 获取当前 Profiler 状态       |
| `save`   | 保存录制数据到 `.raw` 文件      |


#### editor


| Action            | 说明                    |
| ----------------- | --------------------- |
| `status`          | 获取编辑器状态和 Play Mode 信息 |
| `playmode.status` | 获取当前 Play Mode 状态     |
| `playmode.enter`  | 进入 Play Mode          |
| `playmode.exit`   | 退出 Play Mode          |
| `menu.open`       | 按路径执行菜单项              |
| `window.open`     | 按类型名打开编辑器窗口           |
| `console.get`     | 获取编辑器控制台日志            |
| `console.clear`   | 清空编辑器控制台              |


#### project


| Action           | 说明          |
| ---------------- | ----------- |
| `scene.list`     | 列出项目中所有场景   |
| `scene.open`     | 按路径打开场景     |
| `scene.save`     | 保存当前场景      |
| `selection.get`  | 获取当前编辑器选中对象 |
| `selection.set`  | 设置编辑器选中对象   |
| `asset.list`     | 按类型筛选列出资产   |
| `asset.import`   | 按路径导入资产     |
| `asset.reimport` | 按路径重新导入资产   |


#### session


| Action    | 说明            |
| --------- | ------------- |
| `list`    | 列出活跃的 REPL 会话 |
| `inspect` | 查看会话状态        |
| `reset`   | 重置会话的编译器和执行器  |


#### command


| Action | 说明                  |
| ------ | ------------------- |
| `list` | 列出所有已注册命令（内置 + 自定义） |


### 自定义命令

给任意静态方法加上 `[CommandAction]` —— 启动时自动发现，无需注册。参数从 JSON args 中按名称自动绑定。

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    // 最简形式 — 返回 (bool, string) 元组
    [CommandAction("custom", "greet", summary: "Say hello")]
    private static (bool, string) Greet(string name = "World")
    {
        return (true, $"Hello, {name}!");
    }
}
```

需要返回结构化数据时，使用 `CommandResponse`：

```csharp
using Zh1Zh1.CSharpConsole.Service.Commands.Core;
using Zh1Zh1.CSharpConsole.Service.Commands.Routing;

public static class MyCommands
{
    [CommandAction("mygame", "spawn", editorOnly: true, runOnMainThread: true, summary: "Spawn prefab instances")]
    private static CommandResponse Spawn(string prefabPath, int count = 1)
    {
        // ... 实例化逻辑 ...
        return CommandResponseFactory.Ok($"Spawned {count} instance(s)");
    }
}
```

运行 `$unity-cli-refresh-commands` 让 Codex 感知新命令。

### 架构

```
Codex CLI                      Unity Editor
┌──────────────────┐            ┌──────────────────────────┐
│  Skills          │            │  com.zh1zh1.csharpconsole│
│  ┌────────────┐  │            │  ┌────────────────────┐  │
│  │ cli-command│──┼── HTTP ──▶ │  │ ConsoleHttpService │  │
│  │ cli-exec   │  │            │  │  ├─ CommandRouter  │  │
│  └────────────┘  │            │  │  ├─ REPL 编译器     │  │
│                  │            │  │  └─ REPL 执行器     │  │
│  Python CLI      │            │  └────────────────────┘  │
│  ┌────────────┐  │            │                          │
│  │ cs.py      │  │            │  40+ CommandActions      │
│  │ core_bridge│  │            │  (GameObject, Component, │
│  └────────────┘  │            │   Prefab, Material, ...) │
└──────────────────┘            └──────────────────────────┘
```

- **插件层**：Codex CLI 调用的 Skills 和斜杠命令
- **CLI 层**：Python 调度器，将请求序列化为 JSON
- **Unity 层**：[unity-csharpconsole](https://github.com/niqibiao/unity-csharpconsole) — HTTP 服务，自动发现命令处理器，Roslyn C# REPL

自动检测项目根目录和服务端口，无需手动配置。

### 常见问题


| 问题                     | 解决方案                                                       |
| ---------------------- | ---------------------------------------------------------- |
| `service: UNREACHABLE` | 确保 Unity 编辑器已打开并加载了项目                                      |
| `package: NOT FOUND`   | 运行 `$unity-cli-setup` 或检查 `Packages/manifest.json`         |
| 端口冲突                   | 服务会自动切换到下一个可用端口，查看 `Temp/CSharpConsole/refresh_state.json` |
| 找不到命令                  | 确保包编译成功（Unity Console 中无报错）                                |
| 版本不匹配                  | 运行 `$unity-cli-status` 查看版本信息，如协议版本不同请更新包                  |


---

## License

[Apache-2.0](LICENSE)

---

如果这个插件对你有帮助，请给个 Star，让更多人发现它。