---
description: "Refresh cached custom command list from Unity"
---

Sync the custom command catalog from the running Unity Editor.

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" catalog sync --json --project "$(pwd)"
```

Parse the JSON output. Report the summary (added/removed/total) and the catalog file path from `data.catalogFile`.

On first sync for a project, the catalog file defaults to `{project}/.unity-cli/catalog.json` (the path is cached for subsequent runs). To pick a different location once, run:

```bash
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" catalog sync --json --project "$(pwd)" --catalog-path /your/path/catalog.json
```

If the command fails, suggest the user check that Unity Editor is open and the C# Console package is installed.
