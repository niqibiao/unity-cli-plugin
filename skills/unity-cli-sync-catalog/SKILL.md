---
name: unity-cli-sync-catalog
description: >
  Sync command catalog with running Unity Editor to detect new or removed commands
---

Compare the built-in command catalog in `SKILL.md` with the live command list from the running Unity Editor.

Steps:

1. Fetch the live command list:
```bash
python "./plugins/unity-cli-plugin/cli/cs.py" list-commands --json --project "$(pwd)"
```

2. Parse `data.resultJson.commands` from the JSON output. This contains all registered commands (built-in + custom).

3. Compare with the static catalog in `./plugins/unity-cli-plugin/skills/unity-cli-command/SKILL.md`. The built-in namespaces are: editor, gameobject, component, transform, material, prefab, project, scene, screenshot, profiler, session, command.

4. Report differences:
   - **New commands** not in SKILL.md → suggest adding them
   - **Removed commands** in SKILL.md but not live → suggest removing them
   - **Changed signatures** (different args) → suggest updating

5. If custom commands exist outside the built-in namespaces, also run `$unity-cli-refresh-commands` to update the custom command cache.
