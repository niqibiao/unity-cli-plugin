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

PACKAGE_NAME = "com.zh1zh1.csharpconsole"
DEFAULT_SOURCE = "https://github.com/niqibiao/unity-csharpconsole.git"


def find_project_root(hint=None):
    """Walk up from *hint* (or cwd) looking for a Unity project (Assets/ dir)."""
    p = Path(hint).resolve() if hint else Path.cwd().resolve()
    for d in [p, *p.parents]:
        if (d / "Assets").is_dir():
            return d
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


# ── Pre-setup commands (pure stdlib, no core needed) ────────────────────

_PROGRESS_RE = re.compile(r"^(.+?):\s+(\d+)%\s+\((\d+)/(\d+)\)")


def _clone_with_progress(source, dest):
    """Clone a git repo, printing progress at 25% intervals."""
    print(f"Cloning {source}")
    try:
        proc = subprocess.Popen(
            ["git", "clone", "--progress", str(source), str(dest)],
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
        print("Error: git clone failed.", file=sys.stderr)
        return proc.returncode
    print(f"Cloned to {dest}")
    return 0


def cmd_setup(root, args):
    if root is None:
        print("Error: no Unity project found (no Assets/ directory above cwd).", file=sys.stderr)
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
        local_dir = root / "Packages" / PACKAGE_NAME
        if local_dir.exists():
            if PACKAGE_NAME in deps:
                print(f"Already installed (local): {local_dir}")
                return 0
            # Directory exists but not in manifest — just add it
        else:
            rc = _clone_with_progress(source, local_dir)
            if rc != 0:
                return 1

        dep_value = f"file:Packages/{PACKAGE_NAME}"
    else:
        if PACKAGE_NAME in deps:
            print(f"Already installed: {PACKAGE_NAME}")
            return 0
        dep_value = source

    deps[PACKAGE_NAME] = dep_value
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(f"Added {PACKAGE_NAME} to {manifest}")
    print("Open Unity Editor to resolve the package, then run: cs status")
    return 0


def cmd_status(root, args):
    if root is None:
        print("project: NOT FOUND (no Assets/ directory)")
        return 1
    print(f"project: {root}")

    from cli.core_bridge import is_available
    ok = is_available(root)
    print(f"package: {'OK' if ok else 'NOT FOUND'}")
    if not ok:
        return 0

    from cli.core_bridge import ConsoleSession
    try:
        s = ConsoleSession(root, args.ip, args.port, args.mode)
        r = s.health()
        print(f"service: {'OK' if r.get('ok') else 'UNREACHABLE'}")
    except Exception as e:
        print(f"service: ERROR ({e})")
    return 0


# ── Main ────────────────────────────────────────────────────────────────

def main():
    # Shared flags available on every subcommand
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--project", help="Unity project root (auto-detected)")
    shared.add_argument("--ip", default="127.0.0.1")
    shared.add_argument("--port", type=int, default=None)
    shared.add_argument("--mode", choices=["editor", "runtime"], default="editor")
    shared.add_argument("--json", dest="as_json", action="store_true", help="JSON output")

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

    sub.add_parser("list-commands", parents=[shared], help="List available commands")

    sp_cmp = sub.add_parser("complete", parents=[shared], help="Get completions")
    sp_cmp.add_argument("code")
    sp_cmp.add_argument("cursor", type=int)

    args = p.parse_args()
    root = find_project_root(args.project)

    # Auto-detect port from refresh_state.json if not specified
    default_port = 15500 if args.mode == "runtime" else 14500
    if args.port is None and root:
        args.port = detect_port(root) or default_port
    elif args.port is None:
        args.port = default_port

    # Pre-setup commands
    if args.cmd == "setup":
        sys.exit(cmd_setup(root, args))
    if args.cmd == "status":
        sys.exit(cmd_status(root, args))
    if not args.cmd:
        p.print_help()
        sys.exit(1)

    # Post-setup commands
    if root is None:
        print("Error: no Unity project found.", file=sys.stderr)
        sys.exit(1)

    from cli.core_bridge import ConsoleSession
    try:
        s = ConsoleSession(root, args.ip, args.port, args.mode)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    def _refresh():
        r = s.refresh()
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
    }

    result = dispatch[args.cmd]()

    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        s.emit(result)

    sys.exit(result.get("exitCode", 0))


if __name__ == "__main__":
    main()
