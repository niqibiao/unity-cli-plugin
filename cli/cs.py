"""Unity C# Console CLI — thin dispatcher over csharpconsole_core."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure the cli package is importable when run as a standalone script
_CLI_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_CLI_DIR) not in sys.path:
    sys.path.insert(0, os.path.dirname(_CLI_DIR))

from cli import PACKAGE_NAME, DEFAULT_SOURCE, save_pkg_path


def _is_unity_root(d):
    return (d / "Assets").is_dir() and (d / "ProjectSettings").is_dir()


def _scan_children(p):
    """Return the first child directory that is a Unity project root, or None."""
    for d in sorted(p.iterdir()):
        if d.is_dir() and _is_unity_root(d):
            return d
    return None


def find_project_root(hint=None):
    """Locate a Unity project root.

    If *hint* is provided (``--project``), use it directly, scan children,
    or walk up to find the root.  Otherwise: current directory, then children.
    """
    if hint:
        p = Path(hint).resolve()
        if _is_unity_root(p):
            return p
        child = _scan_children(p) if p.is_dir() else None
        if child:
            return child
        # Walk up from hint to find project root
        for parent in p.parents:
            if _is_unity_root(parent):
                return parent
        return None

    cwd = Path.cwd().resolve()

    if _is_unity_root(cwd):
        return cwd

    child = _scan_children(cwd)
    if child:
        return child

    # Walk up from cwd
    for parent in cwd.parents:
        if _is_unity_root(parent):
            return parent

    return None


def detect_port(project_root):
    """Read the effective port from Temp/CSharpConsole/refresh_state.json."""
    state_file = Path(project_root) / "Temp" / "CSharpConsole" / "refresh_state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text("utf-8"))
            port = data.get("effectivePort")
            if port:
                return int(port)
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ── Output helpers ─────────────────────────────────────────────────────

_SLIM_DROP = {"stage", "type", "exitCode", "sessionId", "runId", "mode", "durationMs"}
_HEALTH_DROP = {"ok", "initialized", "isEditor", "port", "refreshing", "editorState",
                "packageVersion", "protocolVersion", "unityVersion", "operation",
                "accepted", "sessionsCleared", "exitPlayModeRequested", "message"}


def _slim_result(result):
    """Strip diagnostic fields from a result dict for compact agent output."""
    out = {k: v for k, v in result.items() if k not in _SLIM_DROP}
    data = out.get("data")
    if isinstance(data, dict):
        # command: flatten resultJson, drop request echo
        if "resultJson" in data:
            out["data"] = data["resultJson"]
        # command echo removal
        elif "command" in data and len(data) == 1:
            out.pop("data", None)
        # health/refresh: strip diagnostic fields
        elif "initialized" in data or "accepted" in data:
            trimmed = {k: v for k, v in data.items() if k not in _HEALTH_DROP}
            out["data"] = trimmed if trimmed else None
    # drop empty/redundant summary/data
    if out.get("summary") in ("", "OK"):
        out.pop("summary", None)
    if not out.get("data"):
        out.pop("data", None)
    return out


# ── Pre-setup commands (pure stdlib, no core needed) ────────────────────

_PROGRESS_RE = re.compile(r"^(.+?):\s+(\d+)%\s+\((\d+)/(\d+)\)")


def _clone_with_progress(source, dest):
    """Clone a git repo, printing progress at 25% intervals."""
    print(f"Cloning {source} (shallow)")
    print("Connecting...", flush=True)
    try:
        proc = subprocess.Popen(
            ["git", "clone", "--depth", "1", "--progress", str(source), str(dest)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print("Error: git is not installed or not on PATH.", file=sys.stderr)
        return 1
    last_phase = None
    last_milestone = -1
    buf = ""
    while True:
        chunk = proc.stderr.read(1)
        if not chunk:
            break
        ch = chunk.decode("utf-8", errors="replace")
        if ch in ("\r", "\n"):
            m = _PROGRESS_RE.match(buf.strip())
            if m:
                phase, pct = m.group(1), int(m.group(2))
                milestone = pct // 25
                if phase != last_phase or milestone > last_milestone:
                    print(f"  {phase}: {pct}%")
                    last_phase = phase
                    last_milestone = milestone
            buf = ""
        else:
            buf += ch
    proc.wait()
    if proc.returncode != 0:
        print("Error: git clone failed. Ask the user to check network/proxy and retry manually.", file=sys.stderr)
        return proc.returncode
    print(f"Cloned to {dest}")
    return 0


def cmd_setup(root, args, agent_root=None):
    if root is None:
        print("Error: no Unity project found. Use --project to specify the path.", file=sys.stderr)
        return 1
    manifest = root / "Packages" / "manifest.json"
    if not manifest.exists():
        print(f"Error: {manifest} not found.", file=sys.stderr)
        return 1

    data = json.loads(manifest.read_text("utf-8"))
    deps = data.setdefault("dependencies", {})

    source = args.source or DEFAULT_SOURCE
    method = args.method or "git"

    if method == "local":
        existing = deps.get(PACKAGE_NAME, "")
        if existing.startswith("file:"):
            local_dir = (manifest.parent / existing[len("file:"):]).resolve()
        else:
            # Use existing file: deps (outside Packages/) as reference path
            ref_parent = None
            for pkg, val in deps.items():
                if pkg == PACKAGE_NAME or not isinstance(val, str):
                    continue
                if not val.startswith("file:"):
                    continue
                rel = val[len("file:"):]
                if rel.startswith("Packages/") or rel.startswith("Packages\\"):
                    continue
                ref_parent = Path(rel).parent
                break
            if ref_parent is not None:
                local_dir = (manifest.parent / ref_parent / PACKAGE_NAME).resolve()
                print(f"Using reference path from existing local package: {ref_parent.as_posix()}/")
            else:
                local_dir = root / "Packages" / PACKAGE_NAME
        rel_path = Path(os.path.relpath(local_dir, manifest.parent)).as_posix()
        dep_value_local = f"file:{rel_path}"
        pkg_json = local_dir / "package.json"
        if pkg_json.is_file():
            if PACKAGE_NAME in deps and deps[PACKAGE_NAME] == dep_value_local:
                print(f"Already installed (local): {local_dir}")
                return 0
            # Directory exists but manifest points elsewhere (e.g. git) — update below
        else:
            # Remove incomplete clone leftovers before retrying
            if local_dir.exists():
                import shutil
                shutil.rmtree(local_dir)
            local_dir.parent.mkdir(parents=True, exist_ok=True)
            rc = _clone_with_progress(source, local_dir)
            if rc != 0:
                return 1

        dep_value = dep_value_local
    else:
        if PACKAGE_NAME in deps:
            print(f"Already installed: {PACKAGE_NAME}")
            return 0
        dep_value = source

    deps[PACKAGE_NAME] = dep_value
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(f"Added {PACKAGE_NAME} to {manifest}")
    # Cache the resolved package path for subsequent CLI commands
    if method == "local":
        save_pkg_path(agent_root, local_dir)
    print("Open Unity Editor to resolve the package, then run: cs status")
    return 0


def cmd_status(root, args, agent_root=None):
    if root is None:
        print("unity_project: NOT FOUND")
        return 1
    print(f"unity_project: {root}")

    from cli.core_bridge import find_package_dir
    pkg_dir = find_package_dir(root, agent_root)
    if pkg_dir:
        print(f"package: {pkg_dir}")
    else:
        print("package: NOT FOUND")
    if not pkg_dir:
        return 0

    from cli.core_bridge import ConsoleSession
    try:
        s = ConsoleSession(root, args.ip, args.port, args.mode, args.timeout, pkg_dir=pkg_dir)
        r = s.health()
        if r.get("ok"):
            data = r.get("data", {})
            print(f"service: OK (port {args.port}, {args.mode})")
            pkg_ver = data.get("packageVersion")
            proto_ver = data.get("protocolVersion")
            unity_ver = data.get("unityVersion")
            if pkg_ver:
                ver_parts = [pkg_ver]
                if proto_ver is not None:
                    ver_parts.append(f"protocol v{proto_ver}")
                if unity_ver:
                    ver_parts.append(f"Unity {unity_ver}")
                print(f"version: {', '.join(ver_parts)}")
        else:
            print("service: UNREACHABLE")
    except Exception as e:
        print(f"service: ERROR ({e})")
    return 0


def cmd_check_update(root, args, agent_root=None):
    from cli.core_bridge import find_package_dir
    pkg_dir = find_package_dir(root, agent_root) if root else None

    if not pkg_dir:
        print("package: NOT FOUND (run 'cs setup' first)")
        return 1

    source = getattr(args, "source", None) or DEFAULT_SOURCE
    from cli.version_check import check_versions
    info = check_versions(pkg_dir, source, timeout=5)

    if args.as_json:
        json.dump({"ok": True, **info}, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    print(f"plugin:    {info['plugin']}")
    print(f"package:   {info['package'] or 'unknown'}")
    print(f"remote:    {info['remote'] or 'unavailable (network error)'}")

    if info["aligned"]:
        pv = info["package"] or "?"
        from cli.version_check import parse_semver
        sv = parse_semver(pv)
        label = f"{sv[0]}.{sv[1]}.x" if sv else pv
        print(f"alignment: \u2713 aligned ({label})")
    else:
        from cli.version_check import parse_semver
        pv_s = parse_semver(info["plugin"])
        kv_s = parse_semver(info["package"])
        pl = f"{pv_s[0]}.{pv_s[1]}.x" if pv_s else info["plugin"]
        kl = f"{kv_s[0]}.{kv_s[1]}.x" if kv_s else info["package"]
        print(f"alignment: \u26a0 plugin {pl} \u2260 package {kl}")

    if info["updateAvailable"]:
        print(f"update:    \u26a0 package {info['package']} \u2192 {info['remote']} available")
        print("hint:      run `cs setup --update` to update the package")
    else:
        print(f"update:    \u2713 up to date")

    return 0


# ── Main ────────────────────────────────────────────────────────────────

def main():
    # Shared flags available on every subcommand
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--project", help="Unity project root (auto-detected)")
    shared.add_argument("--ip", default="127.0.0.1")
    shared.add_argument("--port", type=int, default=None)
    shared.add_argument("--mode", choices=["editor", "runtime"], default="editor")
    shared.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds (default: 30)")
    shared.add_argument("--json", dest="as_json", action="store_true",
                        help="JSON output (compact by default, use --verbose for full)")
    shared.add_argument("--verbose", action="store_true",
                        help="Full JSON output with all diagnostic fields")

    p = argparse.ArgumentParser(prog="cs", description="Unity C# Console CLI", parents=[shared])
    sub = p.add_subparsers(dest="cmd")

    sp_setup = sub.add_parser("setup", parents=[shared], help="Install Unity package")
    sp_setup.add_argument("--source", help="Git URL (default: GitHub repo)")
    sp_setup.add_argument("--method", choices=["local", "git"], default="git",
                          help="git = Unity resolves URL, local = clone to Packages/ (default: git)")

    sub.add_parser("status", parents=[shared], help="Package + connection status")

    sp_exec = sub.add_parser("exec", parents=[shared], help="Execute C# code")
    sp_exec.add_argument("code", help="C# code to execute")

    sp_cmd = sub.add_parser("command", parents=[shared], help="Run framework command")
    sp_cmd.add_argument("namespace", help="Command namespace")
    sp_cmd.add_argument("action", help="Command action")
    sp_cmd.add_argument("args", nargs="?", default=None, help="Arguments (JSON)")

    sub.add_parser("health", parents=[shared], help="Service health check")

    sp_refresh = sub.add_parser("refresh", parents=[shared], help="Trigger asset refresh and script compilation")
    sp_refresh.add_argument("--wait", type=int, nargs="?", const=60, default=None, metavar="TIMEOUT",
                            help="Wait for refresh to complete (default timeout: 60s)")
    sp_refresh.add_argument("--exit-playmode", action="store_true",
                            help="Exit play mode before refreshing if needed")

    sub.add_parser("list-commands", parents=[shared], help="List available commands")

    sp_cmp = sub.add_parser("complete", parents=[shared], help="Get completions")
    sp_cmp.add_argument("code")
    sp_cmp.add_argument("cursor", type=int)

    sp_batch = sub.add_parser("batch", parents=[shared], help="Execute multiple commands in one request")
    sp_batch.add_argument("commands", help="JSON array of commands")
    sp_batch.add_argument("--stop-on-error", action="store_true",
                          help="Stop executing on first error")

    sub.add_parser("check-update", parents=[shared], help="Check version alignment and updates")

    args = p.parse_args()
    agent_root = args.project or str(Path.cwd())
    root = find_project_root(args.project)

    # Auto-detect port if not specified.
    # refresh_state.json contains the editor service port — only use it for editor mode.
    default_port = 15500 if args.mode == "runtime" else 14500
    if args.port is None and root and args.mode != "runtime":
        args.port = detect_port(root) or default_port
    elif args.port is None:
        args.port = default_port

    # Validate --wait range
    if hasattr(args, "wait") and args.wait is not None:
        if args.wait < 0:
            print("Error: --wait timeout must be non-negative.", file=sys.stderr)
            sys.exit(1)
        if args.wait > 300:
            print(f"Warning: --wait capped to 300s (requested {args.wait}s)", file=sys.stderr)
            args.wait = 300

    # Pre-setup commands
    if args.cmd == "setup":
        sys.exit(cmd_setup(root, args, agent_root))
    if args.cmd == "status":
        sys.exit(cmd_status(root, args, agent_root))
    if args.cmd == "check-update":
        sys.exit(cmd_check_update(root, args, agent_root))
    if not args.cmd:
        p.print_help()
        sys.exit(1)

    # Post-setup commands
    if root is None:
        print("Error: no Unity project found. Use --project to specify the path.", file=sys.stderr)
        sys.exit(1)

    from cli.core_bridge import find_package_dir, ConsoleSession
    pkg_dir = find_package_dir(root, agent_root)
    if pkg_dir is None:
        print("Error: C# Console package not found. Run 'cs setup' (or /unity-cli-setup) first.", file=sys.stderr)
        sys.exit(1)

    s = ConsoleSession(root, args.ip, args.port, args.mode, args.timeout, pkg_dir=pkg_dir)

    def _refresh():
        r = s.refresh(exit_playmode=getattr(args, "exit_playmode", False))
        if args.wait is not None:
            if r.get("ok"):
                r = s.wait_ready(timeout=args.wait)
            else:
                print("Warning: refresh returned ok=false; --wait skipped", file=sys.stderr)
        return r

    dispatch = {
        "exec":     lambda: s.exec(args.code),
        "command":  lambda: s.command(args.namespace, args.action, args.args),
        "health":   lambda: s.health(),
        "refresh":  _refresh,
        "list-commands": lambda: s.list_commands(),
        "complete": lambda: s.complete(args.code, args.cursor),
        "batch":    lambda: s.batch(args.commands, args.stop_on_error),
    }

    result = dispatch[args.cmd]()

    if args.as_json:
        if not args.verbose:
            result = _slim_result(result)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        s.emit(result)

    sys.exit(result.get("exitCode", 0))


if __name__ == "__main__":
    main()
