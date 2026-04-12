"""Version alignment checks for unity-cli-plugin."""

import base64
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def parse_semver(version_str):
    """Extract (major, minor, patch) from a version string, or None."""
    if not version_str:
        return None
    m = _SEMVER_RE.search(str(version_str))
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def is_aligned(v1, v2):
    """True if two version strings share the same major.minor."""
    a, b = parse_semver(v1), parse_semver(v2)
    if a is None or b is None:
        return True  # can't compare → assume aligned
    return a[0] == b[0] and a[1] == b[1]


def get_plugin_version():
    """Read plugin version from .claude-plugin/plugin.json. Returns str or 'unknown'."""
    try:
        pj = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
        data = json.loads(pj.read_text("utf-8"))
        return data.get("version", "unknown")
    except Exception:
        return "unknown"


def get_package_version(pkg_dir):
    """Read package version from <pkg_dir>/package.json. Returns str or None."""
    try:
        pj = Path(pkg_dir) / "package.json"
        data = json.loads(pj.read_text("utf-8"))
        return data.get("version")
    except Exception:
        return None


def _github_owner_repo(source):
    """Extract 'owner/repo' from a GitHub URL. Returns str or None."""
    m = re.search(r"github\.com[/:]([^/]+)/([^/.]+?)(?:\.git)?$", str(source))
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def fetch_remote_version(source, timeout=5):
    """Fetch the version from the remote repo's default-branch package.json.

    Primary: GitHub raw URL. Fallback: GitHub contents API.
    Returns version string or None on failure.
    """
    owner_repo = _github_owner_repo(source)
    if not owner_repo:
        return None

    # Primary: raw.githubusercontent.com
    raw_url = f"https://raw.githubusercontent.com/{owner_repo}/main/package.json"
    try:
        req = urllib.request.Request(raw_url, headers={"User-Agent": "unity-cli-plugin"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("version")
    except Exception:
        pass

    # Fallback: GitHub API
    api_url = f"https://api.github.com/repos/{owner_repo}/contents/package.json"
    try:
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "unity-cli-plugin",
            "Accept": "application/vnd.github.v3+json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
            content = base64.b64decode(meta["content"]).decode("utf-8")
            data = json.loads(content)
            return data.get("version")
    except Exception:
        return None


def check_versions(pkg_dir, source, timeout=5):
    """Run all version checks. Returns a dict with structured results.

    Keys: plugin, package, remote, aligned, updateAvailable
    """
    plugin_ver = get_plugin_version()
    package_ver = get_package_version(pkg_dir)
    remote_ver = fetch_remote_version(source, timeout=timeout)

    aligned = is_aligned(plugin_ver, package_ver) if package_ver else True
    update_available = False
    if remote_ver and package_ver:
        rv, pv = parse_semver(remote_ver), parse_semver(package_ver)
        if rv and pv:
            update_available = rv > pv

    return {
        "plugin": plugin_ver,
        "package": package_ver,
        "remote": remote_ver,
        "aligned": aligned,
        "updateAvailable": update_available,
    }
