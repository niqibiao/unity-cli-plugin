---
description: "Refresh cached custom command list from Unity"
---

Sync the custom command catalog from the running Unity Editor.

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" catalog sync --json --project "$(pwd)"
```

Parse the JSON output. Report the summary (added/removed/total).

If the command fails, suggest the user check that Unity Editor is open and the C# Console package is installed.
