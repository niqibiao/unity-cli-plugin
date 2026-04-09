"""Unity C# Console CLI package."""

import json
from pathlib import Path

PACKAGE_NAME = "com.zh1zh1.csharpconsole"
DEFAULT_SOURCE = "https://github.com/niqibiao/unity-csharpconsole.git"

# Cache file lives in the plugin directory, keyed by agent working directory.
_PLUGIN_DIR = Path(__file__).resolve().parent.parent
_CACHE_FILE = _PLUGIN_DIR / ".pkg-cache.json"


def _load_cache():
    try:
        return json.loads(_CACHE_FILE.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(data):
    _CACHE_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8"
    )


def _agent_key(agent_root):
    """Normalize agent working directory to a stable cache key."""
    return str(Path(agent_root).resolve())


def save_pkg_path(agent_root, pkg_dir):
    """Cache the resolved package directory, keyed by agent working directory."""
    key = _agent_key(agent_root)
    data = _load_cache()
    data[key] = str(Path(pkg_dir).resolve())
    _save_cache(data)


def load_pkg_path(agent_root):
    """Load cached package directory for an agent root, or None if missing/invalid."""
    key = _agent_key(agent_root)
    data = _load_cache()
    path = data.get(key)
    if path:
        p = Path(path)
        if p.is_dir():
            return p
    return None
