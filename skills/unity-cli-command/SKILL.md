---
name: unity-cli-command
description: >
  Structured Unity Editor commands. Covers: GameObject (create/find/modify/destroy/duplicate),
  component (add/remove/get/modify), transform (get/set), scene management, materials,
  prefabs, screenshots, play mode, profiling, hierarchy query, asset refresh/recompile,
  asset management (move/copy/delete/create_folder), selection, session, command listing.
  Preferred over raw C# execution.
---

# Unity CLI Command

Run framework commands in the Unity Editor via the C# Console command protocol.

## Command-First Principle

Always prefer `cs command` over `cs exec` when a built-in framework command exists. Only fall back to `cs exec` for ad-hoc C# that no existing command covers.

## Usage

```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" command --json --project "$(pwd)" <namespace> <action> ['<args-json>']
```

## Asset Refresh

After writing `.cs` files or modifying assets on disk, follow the `/unity-cli-refresh` procedure (checks play mode + compilation preference, exits play mode if needed, triggers refresh and waits for completion). REPL sessions are cleared on domain reload.

## Identifier Convention

Many commands accept both `path` (hierarchy path like `"Canvas/Button"`) and `instanceId` (int). Use whichever is available — `path` for human-readable references, `instanceId` when you have it from a prior command result. You never need both.

## Built-in Command Catalog

### editor

| action | summary | args |
|--------|---------|------|
| status | Get editor state and play mode info | — |
| playmode.status | Get current play mode state | — |
| playmode.enter | Enter play mode | — |
| playmode.exit | Exit play mode | — |
| menu.open | Open a menu item by path | menuPath: string |
| window.open | Open an editor window by type name | typeName: string, utility: bool |
| console.clear | Clear the editor console | — |
| console.mark | Write a searchable marker into the editor log and return the log file path | label: string |

### gameobject

| action | summary | args |
|--------|---------|------|
| find | Find GameObjects by name, tag, or component type | name: string, tag: string, componentType: string |
| create | Create a new GameObject (empty or primitive) | name: string, primitiveType: string, parentPath: string |
| destroy | Destroy a GameObject | path: string, instanceId: int |
| get | Get detailed info about a GameObject | path: string, instanceId: int |
| modify | Modify a GameObject's basic properties | path: string, instanceId: int, name: string, tag: string, layer: int, active: int, isStatic: int |
| set_parent | Change a GameObject's parent | path: string, instanceId: int, parentPath: string, parentInstanceId: int, worldPositionStays: bool |
| duplicate | Duplicate a GameObject | path: string, instanceId: int, newName: string |

### component

| action | summary | args |
|--------|---------|------|
| add | Add a component to a GameObject | typeName: string, gameObjectPath: string, gameObjectInstanceId: int |
| remove | Remove a component from a GameObject | typeName: string, gameObjectPath: string, gameObjectInstanceId: int, index: int |
| get | Get serialized field data of a component | typeName: string, gameObjectPath: string, gameObjectInstanceId: int, index: int |
| modify | Modify serialized fields of a component | fields: FieldPair[], typeName: string, gameObjectPath: string, gameObjectInstanceId: int, index: int |

### transform

| action | summary | args |
|--------|---------|------|
| get | Get a GameObject's transform values | path: string, instanceId: int |
| set | Set a GameObject's transform values | path: string, instanceId: int, position: Vector3, rotation: Vector3, scale: Vector3, local: bool |

### material

| action | summary | args |
|--------|---------|------|
| create | Create a new material asset | savePath: string, shaderName: string |
| get | Get material properties | assetPath: string, gameObjectPath: string |
| assign | Assign a material to a Renderer component | materialPath: string, gameObjectPath: string, gameObjectInstanceId: int, index: int |

### prefab

| action | summary | args |
|--------|---------|------|
| create | Create a prefab asset from a scene GameObject | savePath: string, gameObjectPath: string, gameObjectInstanceId: int |
| instantiate | Instantiate a prefab into the active scene | assetPath: string, parentPath: string, position: Vector3 |
| unpack | Unpack a prefab instance | gameObjectPath: string, gameObjectInstanceId: int, full: bool |

### project

| action | summary | args |
|--------|---------|------|
| scene.list | List all scenes in the project | — |
| scene.open | Open a scene by path | scenePath: string, mode: string |
| scene.save | Save the current scene | scenePath: string, saveAsCopy: bool |
| selection.get | Get the current editor selection | — |
| selection.set | Set the editor selection by name or path | instanceIds: int[], assetPaths: string[] |
| asset.list | List assets by type filter | filter: string, folders: string[] |
| asset.import | Import an asset by path | assetPath: string, forceSynchronousImport: bool |
| asset.reimport | Reimport an asset by path | assetPath: string, forceSynchronousImport: bool |

### asset

| action | summary | args |
|--------|---------|------|
| move | Move or rename an asset | sourcePath: string, destinationPath: string |
| copy | Copy an asset to a new path | sourcePath: string, destinationPath: string |
| delete | Delete one or more assets | assetPath: string, assetPaths: string[] |
| create_folder | Create a folder in the Asset Database | folderPath: string |

### scene

| action | summary | args |
|--------|---------|------|
| hierarchy | Get the full scene hierarchy tree | depth: int, includeComponents: bool |

### screenshot

| action | summary | args |
|--------|---------|------|
| scene_view | Capture the current Scene View | savePath: string, width: int, height: int |
| game_view | Capture the Game View | savePath: string, width: int, height: int, superSize: int |

### profiler

| action | summary | args |
|--------|---------|------|
| start | Start Profiler recording | deep: bool, logFile: string |
| stop | Stop Profiler recording | — |
| status | Get current Profiler state | — |
| save | Save recorded profiler data to a .raw file | savePath: string |

### session

| action | summary | args |
|--------|---------|------|
| list | List active REPL sessions | — |
| inspect | Inspect a session's state | — |
| reset | Reset a session's compiler and executor | — |

### command

| action | summary | args |
|--------|---------|------|
| list | List registered commands | — |

## Custom Commands

1. Check if `${CLAUDE_PLUGIN_ROOT}/skills/unity-cli-command/dynamic-commands.md` exists and Read it for additional commands.
2. If no match found, run `cs list-commands --json` as fallback and suggest `/unity-cli-refresh-commands`.

## Runtime Mode

Most commands are **editor-only** (require the Unity Editor, not a standalone player). The `session/*` and `command/list` commands work in both editor and runtime modes. Pass `--mode runtime --port 15500` for player builds.

## Examples

Base command for all examples:

```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" command --json --project "$(pwd)" <namespace> <action> ['<args-json>']
```

```bash
# No-arg command
... editor status

# Create a cube
... gameobject create '{"name":"Wall","primitiveType":"Cube"}'

# Move it (Vector3 as {x,y,z} object)
... transform set '{"path":"Wall","position":{"x":0,"y":1,"z":3}}'

# Get component data
... component get '{"gameObjectPath":"Main Camera","typeName":"Camera"}'

# Screenshot
... screenshot scene_view '{"savePath":"Assets/screenshot.png"}'

# Scene hierarchy with components
... scene hierarchy '{"depth":3,"includeComponents":true}'

# Discover all commands (including custom)
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" list-commands --json --project "$(pwd)"
```

## Workflow

1. Match the user's intent to a namespace + action from the catalog above
2. Run the command with appropriate args
3. **After writing C# files**, follow the Asset Refresh procedure above (check play mode → exit if needed → refresh)
4. If no matching command exists in the catalog, check `dynamic-commands.md` for custom commands
5. If still no match, run `list-commands` as a one-time fallback and suggest `/unity-cli-refresh-commands`
6. If no command covers the request at all, fall back to the `unity-cli-exec-code` skill
