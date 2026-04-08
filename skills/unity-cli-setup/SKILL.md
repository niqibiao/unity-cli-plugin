---
name: unity-cli-setup
description: >
  Install Unity C# Console package into the current Unity project
---

Install the C# Console Unity package into the current project.

Before running the command, ask the user to choose an installation method:

1. **git** (recommended) — writes the git URL to manifest.json, Unity resolves it on its own
2. **local** — clones the repo into `Packages/com.zh1zh1.csharpconsole/`, suitable for development and debugging

Then run:
```bash
python "${CODEX_PLUGIN_ROOT}/cli/cs.py" setup --project "$(pwd)" --method <local|git>
```

After running, instruct the user to:
1. Open the Unity Editor for the target project
2. Wait for the package manager to resolve `com.zh1zh1.csharpconsole`
3. Run `$unity-cli-status` to verify installation and service connectivity
