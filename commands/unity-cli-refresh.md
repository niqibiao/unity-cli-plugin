---
description: "Trigger Unity AssetDatabase refresh and wait for script compilation"
---

Trigger Unity to re-scan assets and recompile scripts. Use after writing or modifying `.cs` files on disk.

Steps:

1. Check play mode and compilation preference:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" command --json --project "$(pwd)" editor playmode.status
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" exec --json --project "$(pwd)" "UnityEditor.EditorPrefs.GetInt(\"ScriptCompilationDuringPlay\", 0)"
```
Preference values: `0` = RecompileAndContinue, `1` = RecompileAfterFinished, `2` = StopAndRecompile.

2. If `isPlaying: true` and preference is `1`: Unity will not compile until play mode ends. Ask the user whether to exit play mode. If confirmed:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" command --json --project "$(pwd)" editor playmode.exit
```
Wait a few seconds for the transition to complete.
- If preference is `0`: proceed directly, Unity recompiles and continues playing.
- If preference is `2`: Unity auto-stops play mode on script changes, no manual exit needed.

3. Trigger refresh:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" refresh --json --project "$(pwd)" --wait 60
```

- `--wait TIMEOUT` blocks until the refresh + compile + domain-reload cycle completes (default 60s)
- Omit `--wait` for fire-and-forget (trigger only, don't wait)
- Domain reload restarts the HTTP service and clears REPL sessions; `--wait` handles reconnection

After completion, verify with `/unity-cli-status` if needed.
