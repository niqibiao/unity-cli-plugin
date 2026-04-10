---
name: unity-cli-refresh
description: >
  Trigger Unity AssetDatabase refresh and wait for script compilation
---

Trigger Unity to re-scan assets and recompile scripts. Use after writing or modifying `.cs` files on disk.

**Recommended (one-step):**

```bash
python "./plugins/unity-cli-plugin/cli/cs.py" refresh --json --project "$(pwd)" --exit-playmode --wait 60
```

- `--exit-playmode` automatically exits play mode before refreshing if needed
- `--wait TIMEOUT` blocks until the refresh + compile + domain-reload cycle completes (default 60s)
- Domain reload restarts the HTTP service and clears REPL sessions; `--wait` handles reconnection

After completion, verify with `$unity-cli-status` if needed.

**Manual control (when you need fine-grained steps):**

1. Check play mode:
```bash
python "./plugins/unity-cli-plugin/cli/cs.py" command --json --project "$(pwd)" editor playmode.status
```

2. If `isPlaying: true` and you need to exit first:
```bash
python "./plugins/unity-cli-plugin/cli/cs.py" command --json --project "$(pwd)" editor playmode.exit
```

3. Trigger refresh without `--exit-playmode`:
```bash
python "./plugins/unity-cli-plugin/cli/cs.py" refresh --json --project "$(pwd)" --wait 60
```
