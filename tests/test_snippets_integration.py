"""Live-Unity integration tests for the snippet submission path.

These require a running Unity Editor with com.zh1zh1.csharpconsole on the
target project. They auto-skip when the service is unreachable, so they are
safe in CI / headless environments.

Target project (must have the package + a running editor on port 14500):

    UNITY_CLI_IT_PROJECT=E:/path/to/UnityProject   # default: PackagesDemo

Run just these:

    python -m unittest tests.test_snippets_integration -v
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli.snippets.render import render_submission

DEFAULT_PROJECT = "E:/UnityProjects/PackagesDemo"


def _project():
    return os.environ.get("UNITY_CLI_IT_PROJECT", DEFAULT_PROJECT)


class SnippetLiveSubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cli.core_bridge import find_package_dir, ConsoleSession

        proj = _project()
        if not (Path(proj) / "Assets").is_dir():
            raise unittest.SkipTest(f"not a Unity project: {proj}")
        pkg = find_package_dir(proj, None)
        if pkg is None:
            raise unittest.SkipTest(f"csharpconsole package not found under {proj}")
        cls.session = ConsoleSession(proj, pkg_dir=pkg, timeout=8)
        health = cls.session.health()
        if not health.get("ok"):
            raise unittest.SkipTest(
                f"Unity service not reachable at {proj}: {health.get('summary')}"
            )

    def _run(self, body, schema, args):
        submission = render_submission("it.probe", body, schema, args)
        return submission, self.session.exec(submission)

    def test_unmodified_private_run_compiles_and_runs(self):
        """The authoring convention writes `static Run` with NO access
        modifier (default private). The generated wrapper calls it from
        OUTSIDE the class. Standard Roslyn rejects that with CS0122; it only
        compiles because the service sets Roslyn's IgnoreAccessibility binder
        flag via reflection. This is the load-bearing assumption of the whole
        snippet design — if it ever breaks, every snippet breaks.
        """
        body = 'static string Run(string s) { return s + "!"; }'
        schema = [{"name": "s", "type": "string"}]
        submission, resp = self._run(body, schema, {"s": "hi"})
        self.assertTrue(
            resp.get("ok"),
            "private Run failed to compile/run — IgnoreAccessibility hack may "
            f"be ineffective.\n--- submission ---\n{submission}\n"
            f"--- response ---\n{resp}",
        )
        self.assertEqual(resp.get("exitCode", 0), 0)
        self.assertIn("hi!", (resp.get("data") or {}).get("text", ""))

    def test_internal_run_control(self):
        """Control: an explicit `internal static Run` must also work, so a
        failure of the test above is attributable to the access modifier and
        not to the wrapper shape in general."""
        body = 'internal static string Run(string s) { return s + "?"; }'
        schema = [{"name": "s", "type": "string"}]
        submission, resp = self._run(body, schema, {"s": "hi"})
        self.assertTrue(resp.get("ok"), f"{submission}\n{resp}")
        self.assertIn("hi?", (resp.get("data") or {}).get("text", ""))

    def test_result_arrives_as_data_text_tostring(self):
        """Confirms the `expected` design premise: exec returns the result as
        ToString() text in data.text, never structured JSON. A List<string>
        stringifies to its type name — which is exactly why `expected` is a
        string compared against data.text rather than a JSON deep-equal."""
        body = (
            "using System.Collections.Generic;\n"
            'static List<string> Run() { return new List<string>{ "a", "b" }; }'
        )
        submission, resp = self._run(body, [], {})
        self.assertTrue(resp.get("ok"), f"{submission}\n{resp}")
        text = (resp.get("data") or {}).get("text", "")
        self.assertIn("List", text)          # ToString of the type, not JSON
        self.assertNotIn('["a"', text)


if __name__ == "__main__":
    unittest.main()
