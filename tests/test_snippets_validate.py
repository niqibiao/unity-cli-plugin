import unittest

from cli.snippets.validate import validate_snippet, ValidationError


SAMPLE_SNIPPET = {
    "id": "scene.find_in_layer",
    "summary": "Find in layer",
    "safety": "read-only",
    "args": [{"name": "layerName", "type": "string"}],
    "example": {"layerName": "Default"},
    "body": (
        "using System.Linq;\n"
        "static List<string> Run(string layerName) {\n"
        "    return new List<string> { layerName };\n"
        "}"
    ),
}


def _ok_response(text="Default"):
    # Mirrors the real exec response shape: the service ToString()s the
    # result into data.text (never structured JSON).
    return {"ok": True, "exitCode": 0, "data": {"text": text}}


def _err_response(summary="compile error"):
    return {"ok": False, "exitCode": 1, "summary": summary}


class ValidateReadOnlyTests(unittest.TestCase):
    def test_passes_when_response_ok(self):
        calls = []
        def fake_runner(code):
            calls.append(code)
            return _ok_response()
        validate_snippet(SAMPLE_SNIPPET, fake_runner)
        self.assertEqual(len(calls), 1)
        self.assertIn("static class __Snip_", calls[0])
        self.assertIn(".Run(\"Default\")", calls[0])

    def test_fails_when_response_not_ok(self):
        def fake_runner(code):
            return _err_response("compile error: bad syntax")
        with self.assertRaises(ValidationError) as ctx:
            validate_snippet(SAMPLE_SNIPPET, fake_runner)
        self.assertIn("compile error", str(ctx.exception))

    def test_expected_match_passes(self):
        snip = dict(SAMPLE_SNIPPET, expected="Default")
        def fake_runner(code):
            return _ok_response("Default")
        validate_snippet(snip, fake_runner)

    def test_expected_mismatch_fails(self):
        snip = dict(SAMPLE_SNIPPET, expected="Default")
        def fake_runner(code):
            return _ok_response("Other")
        with self.assertRaises(ValidationError) as ctx:
            validate_snippet(snip, fake_runner)
        self.assertIn("expected", str(ctx.exception).lower())

    def test_expected_fails_when_response_has_no_text(self):
        snip = dict(SAMPLE_SNIPPET, expected="Default")
        def fake_runner(code):
            return {"ok": True, "exitCode": 0, "data": {}}
        with self.assertRaises(ValidationError):
            validate_snippet(snip, fake_runner)

    def test_mutates_refused_without_flag(self):
        snip = dict(SAMPLE_SNIPPET, safety="mutates")
        def fake_runner(code):
            self.fail("runner should not be called for mutates without --no-validate")
        with self.assertRaises(ValidationError):
            validate_snippet(snip, fake_runner)

    def test_mutates_skipped_with_no_validate(self):
        snip = dict(SAMPLE_SNIPPET, safety="mutates")
        calls = []
        def fake_runner(code):
            calls.append(code)
            return _ok_response()
        validate_snippet(snip, fake_runner, no_validate=True)
        self.assertEqual(calls, [])


class MutatesRoutingTests(unittest.TestCase):
    def test_mutates_with_no_validate_skips_runner(self):
        snip = dict(SAMPLE_SNIPPET, safety="mutates")
        calls = []
        def fake_runner(code):
            calls.append(code)
            return _ok_response()
        validate_snippet(snip, fake_runner, no_validate=True)
        self.assertEqual(calls, [])

    def test_mutates_no_no_validate_raises_before_runner(self):
        snip = dict(SAMPLE_SNIPPET, safety="mutates")
        def fake_runner(code):
            self.fail("runner must not be called for mutates without --no-validate")
        with self.assertRaises(ValidationError):
            validate_snippet(snip, fake_runner)


if __name__ == "__main__":
    unittest.main()
