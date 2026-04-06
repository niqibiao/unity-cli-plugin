"""Dynamic bridge to csharpconsole_core from an installed Unity package."""

import os
import sys
from pathlib import Path

PACKAGE_NAME = "com.zh1zh1.csharpconsole"
CORE_RELATIVE = Path("Editor/ExternalTool~/console-client")


def resolve(project_root):
    """Find the csharpconsole_core directory. Returns Path or raises FileNotFoundError."""
    env = os.environ.get("CS_CORE_PATH")
    if env:
        p = Path(env)
        if (p / "csharpconsole_core").is_dir():
            return p

    local = Path(project_root) / "Packages" / PACKAGE_NAME / CORE_RELATIVE
    if (local / "csharpconsole_core").is_dir():
        return local

    cache_dir = Path(project_root) / "Library" / "PackageCache"
    if cache_dir.is_dir():
        for d in cache_dir.iterdir():
            if d.name == PACKAGE_NAME or d.name.startswith(PACKAGE_NAME + "@"):
                candidate = d / CORE_RELATIVE
                if (candidate / "csharpconsole_core").is_dir():
                    return candidate

    raise FileNotFoundError(
        f"csharpconsole_core not found in {project_root}. Run 'cs setup' first."
    )


def is_available(project_root):
    try:
        resolve(project_root)
        return True
    except FileNotFoundError:
        return False


def _ensure_path(core_path):
    """Add core_path and its site-packages to sys.path if needed."""
    s = str(core_path)
    if s not in sys.path:
        sys.path.insert(0, s)
    sp = os.path.join(s, "site-packages")
    if os.path.isdir(sp) and sp not in sys.path:
        sys.path.insert(0, sp)


class ConsoleSession:
    """Pre-wired facade over csharpconsole_core. One-liner per command."""

    def __init__(self, project_root, ip="127.0.0.1", port=14500, mode="editor"):
        core_path = resolve(project_root)
        _ensure_path(core_path)

        from csharpconsole_core import (
            client_base, command_protocol, config_base,
            output, response_parser, transport_http,
        )
        self._client = client_base
        self._cmd = command_protocol
        self._parser = response_parser
        self._output = output

        state = config_base.SharedConfigState()
        state.ip = ip
        state.port = port
        state.runtime_mode = mode == "runtime"
        self._state = state

        self._session_id = client_base.generate_session_id(None)
        self._post = lambda ep, pl, t=30: transport_http.post_json(
            state.current_server_base_url(), ep, pl, t
        )
        self._mode_name = lambda: state.current_mode_name()
        self._define = lambda: ""
        self._using = lambda: ""

    def exec(self, code, reset=False):
        return self._client.execute_editor_request(
            self._post, self._parser.parse_text_http_response,
            self._define, self._using, code, self._session_id, reset,
        )

    def command(self, namespace, action, args=None):
        return self._cmd.request_command(
            self._post, self._parser.parse_command_http_response,
            self._mode_name, namespace, action, self._session_id, args,
        )

    def health(self):
        return self._client.request_health(
            self._post, self._parser.parse_health_http_response, self._mode_name,
        )

    def complete(self, code, cursor):
        return self._client.request_completion(
            self._post, self._parser.parse_completion_http_response,
            self._mode_name, self._define, self._using,
            self._state.runtime_mode, self._state.runtime_dll_path,
            code, cursor, self._session_id,
        )

    def refresh(self):
        return self._client.request_refresh(
            self._post, self._parser.parse_refresh_http_response, self._mode_name,
        )

    def wait_ready(self, timeout=60):
        return self._client.wait_for_service_recovery(
            self.health, self._mode_name, timeout,
        )

    def list_commands(self):
        return self.command("command", "list")

    def emit(self, result):
        self._output.emit_result(result, as_json=False)
