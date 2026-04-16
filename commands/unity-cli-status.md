---
description: "Show Unity package installation and service connection status"
---

Check the current state of the Unity C# Console plugin: package installation and service connectivity.

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" status --project "$(pwd)"
```

Reports:
- **project**: Unity project root path
- **package**: whether `com.zh1zh1.csharpconsole` is installed and resolvable
- **service**: whether the Unity HTTP service is reachable at the configured port

**Version mismatch handling**: If the output contains `⚠` indicating plugin/package version misalignment, do NOT just report the mismatch. Directly ask the user whether they want to update the package now. If they confirm, run `/unity-cli-setup` to perform the update.
