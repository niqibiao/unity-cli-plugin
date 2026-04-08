"""Unity C# Console CLI package."""

import json
from pathlib import Path

PACKAGE_NAME = "com.zh1zh1.csharpconsole"
DEFAULT_SOURCE = "https://github.com/niqibiao/unity-csharpconsole.git"

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_CACHE_FILE = _PLUGIN_ROOT / ".cache" / "project_cache.json"


def _load_cache():
    try:
        return json.loads(_CACHE_FILE.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache):
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), "utf-8")


def save_pkg_path(project_root, pkg_dir):
    """Cache the resolved package installation directory for a project."""
    cache = _load_cache()
    key = f"pkg:{Path(project_root).resolve()}"
    cache[key] = str(Path(pkg_dir).resolve())
    _save_cache(cache)


def load_pkg_path(project_root):
    """Load cached package installation directory, or None if missing/invalid."""
    cache = _load_cache()
    key = f"pkg:{Path(project_root).resolve()}"
    path_str = cache.get(key)
    if path_str:
        p = Path(path_str)
        if p.is_dir():
            return p
    return None


def save_project_root(cwd, root):
    """Cache the resolved Unity project root for a working directory."""
    cache = _load_cache()
    cache[str(cwd)] = str(root)
    _save_cache(cache)


def load_project_root(cwd, validator=None):
    """Load cached project root for a working directory, or None.

    *validator*, if provided, is called with the cached Path; return
    ``None`` when the check fails so the caller can re-resolve.
    """
    cache = _load_cache()
    path_str = cache.get(str(cwd))
    if path_str:
        p = Path(path_str)
        if validator is None or validator(p):
            return p
    return None
