---
name: unity-cli-setup
description: >
  Install Unity C# Console package into the current Unity project
---

Install the C# Console Unity package into the current project.

Before running the command, ask the user to choose an installation method:

1. **git** (recommended) — writes the git URL to manifest.json, Unity resolves it on its own
2. **local** — clones the repo locally, suitable for development and debugging (uses existing local package path if found, otherwise defaults to `Packages/`)

Then run:
```bash
python "./plugins/unity-cli-plugin/cli/cs.py" setup --project "$(pwd)" --method <local|git>
```

By default the package is pinned to the latest `vMAJOR.MINOR.*` tag matching the plugin version. Append `--no-pin` to install from HEAD instead. With `--method local`, the clone ends in detached HEAD at the pinned tag; if the user wants to develop in the clone, instruct them to `git checkout main` afterward.

**If the command fails (non-zero exit code), stop immediately.** Do not retry, do not attempt manual git clone or alternative approaches. Report the error to the user and ask them to resolve the issue (e.g. network, proxy, git config) before retrying `$unity-cli-setup`.

**Version mismatch handling**: If the output contains `⚠ version mismatch`, do NOT just report it. Directly ask the user whether they want to update the package now. If they confirm, re-run the setup command with `--update` appended.

After a successful run (with no version mismatch), instruct the user to:
1. Open the Unity Editor for the target project
2. Wait for the package manager to resolve `com.zh1zh1.csharpconsole`
3. Run `$unity-cli-status` to verify installation and service connectivity
