# Self-Evolving Snippet Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a project-local library of reusable C# snippets executed via `cs exec`, with a validation gate, usage tracking, automatic aging, and a `unity-cli-snippets` skill that drives agent discovery and self-evolution.

**Architecture:** Three new Python modules under `cli/snippets/` (render, store, validate, stats), wired into `cli/cs.py` as a `cs snippets` subcommand family. Snippet bodies are markdown files with frontmatter + a `static Run(...)` C# method, stored at `.unity-cli/snippets~/<id>.md`. The CLI wraps each submission in a unique `static class __Snip_<hash>` to isolate symbols across REPL sessions. Stats and audit live in separate JSON files (audit committed, stats gitignored) to avoid PR churn.

**Tech Stack:** Python 3.7+ stdlib only (argparse, json, hashlib, pathlib, re, datetime, unittest). Tests use `unittest` (stdlib); no test framework added.

**Spec:** `docs/superpowers/specs/2026-05-07-self-evolving-snippets-design.md` (commit `1d80675`)

**Phasing:**

- **D0 (Tasks 1–10):** Minimal validated loop — render + store + validate-readonly + stats; CLI: `add`, `use`, `list`, `show`. End-to-end smoke test on a real Unity project. Independently shippable.
- **D1 (Tasks 11–17):** Remaining CLI — `search`, `update`, `deprecate`, `prune`, `stats`. Aging policy. Mutates-class refusal. Independently shippable.
- **D2 (Tasks 18–23):** Skill + cross-references + docs + `.gitignore` integration in `cs setup`.

**Note on tests:** This plan introduces `tests/` to the repo (currently no-tests). Tests use stdlib `unittest` only — no external deps, no build step, runnable via `python -m unittest discover tests`. This stays within the project's "stdlib-only" character.

**Note on Roslyn submissions:** Throughout this plan, the C# REPL session is reached through the existing `ConsoleSession` facade in `cli/core_bridge.py`. Its `exec` method takes a code string and returns the standard envelope. Plan code samples often alias it to a local `exec_fn` to keep call sites uniform between production code (where the session provides it) and tests (where a fake function is injected).

---

## Phase D0 — Minimal Validated Loop

### Task 1: Type substitution renderer (`render.py` — typed literals)

**Files:**
- Create: `cli/snippets/__init__.py`
- Create: `cli/snippets/render.py`
- Create: `tests/__init__.py`
- Create: `tests/test_snippets_render.py`

- [ ] **Step 1: Create empty package init files**

`cli/snippets/__init__.py`:
```python
"""Snippet library: render, store, validate, stats."""
```

`tests/__init__.py`:
```python
```

- [ ] **Step 2: Write the failing test**

`tests/test_snippets_render.py`:
```python
import unittest

from cli.snippets.render import render_literal


class RenderLiteralTests(unittest.TestCase):
    def test_string_basic(self):
        self.assertEqual(render_literal("string", "hello"), '"hello"')

    def test_string_escapes_quotes(self):
        self.assertEqual(render_literal("string", 'he said "hi"'),
                         '"he said \\"hi\\""')

    def test_string_escapes_newline(self):
        self.assertEqual(render_literal("string", "a\nb"), '"a\\nb"')

    def test_int(self):
        self.assertEqual(render_literal("int", 42), "42")

    def test_float_with_suffix(self):
        self.assertEqual(render_literal("float", 3.14), "3.14f")

    def test_float_integer_value(self):
        self.assertEqual(render_literal("float", 5), "5f")

    def test_bool_true(self):
        self.assertEqual(render_literal("bool", True), "true")

    def test_bool_false(self):
        self.assertEqual(render_literal("bool", False), "false")

    def test_vector2(self):
        self.assertEqual(render_literal("vector2", [1, 2]),
                         "new UnityEngine.Vector2(1f, 2f)")

    def test_vector3(self):
        self.assertEqual(render_literal("vector3", [1.5, 2, 3]),
                         "new UnityEngine.Vector3(1.5f, 2f, 3f)")

    def test_vector4(self):
        self.assertEqual(render_literal("vector4", [1, 2, 3, 4]),
                         "new UnityEngine.Vector4(1f, 2f, 3f, 4f)")

    def test_color_rgb_defaults_alpha(self):
        self.assertEqual(render_literal("color", [1, 0, 0]),
                         "new UnityEngine.Color(1f, 0f, 0f, 1f)")

    def test_color_rgba(self):
        self.assertEqual(render_literal("color", [1, 0, 0, 0.5]),
                         "new UnityEngine.Color(1f, 0f, 0f, 0.5f)")

    def test_string_array(self):
        self.assertEqual(render_literal("string[]", ["a", "b"]),
                         'new string[] { "a", "b" }')

    def test_int_array(self):
        self.assertEqual(render_literal("int[]", [1, 2, 3]),
                         "new int[] { 1, 2, 3 }")

    def test_float_array(self):
        self.assertEqual(render_literal("float[]", [1.0, 2.5]),
                         "new float[] { 1f, 2.5f }")

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            render_literal("expr", "Camera.main")

    def test_vector_wrong_arity_raises(self):
        with self.assertRaises(ValueError):
            render_literal("vector3", [1, 2])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test, verify it fails**

```
python -m unittest tests.test_snippets_render -v
```

Expected: ImportError (module `cli.snippets.render` does not exist yet).

- [ ] **Step 4: Implement the renderer**

`cli/snippets/render.py`:
```python
"""Type-safe substitution of JSON arg values into C# literals."""

import json


def _float_lit(v):
    """Render a float literal, dropping the decimal point only when integral."""
    if isinstance(v, bool):
        raise ValueError("bool not accepted as float")
    f = float(v)
    if f == int(f):
        return f"{int(f)}f"
    return f"{f}f"


def _check_arity(name, value, expected):
    if not isinstance(value, list) or len(value) != expected:
        raise ValueError(
            f"{name} expects a list of {expected} numbers, got {value!r}"
        )


def render_literal(type_name, value):
    """Convert a JSON-decoded *value* into a C# literal expression for *type_name*.

    Generated identifiers are fully qualified (UnityEngine.Vector3 etc.) so the
    call line does not depend on what `using` directives the snippet body has.
    """
    if type_name == "string":
        if not isinstance(value, str):
            raise ValueError(f"string expects a JSON string, got {value!r}")
        return json.dumps(value, ensure_ascii=False)

    if type_name == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"int expects an integer, got {value!r}")
        return str(value)

    if type_name == "float":
        return _float_lit(value)

    if type_name == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"bool expects true/false, got {value!r}")
        return "true" if value else "false"

    if type_name == "vector2":
        _check_arity("vector2", value, 2)
        return f"new UnityEngine.Vector2({_float_lit(value[0])}, {_float_lit(value[1])})"

    if type_name == "vector3":
        _check_arity("vector3", value, 3)
        parts = ", ".join(_float_lit(v) for v in value)
        return f"new UnityEngine.Vector3({parts})"

    if type_name == "vector4":
        _check_arity("vector4", value, 4)
        parts = ", ".join(_float_lit(v) for v in value)
        return f"new UnityEngine.Vector4({parts})"

    if type_name == "color":
        if not isinstance(value, list) or len(value) not in (3, 4):
            raise ValueError(f"color expects [r,g,b] or [r,g,b,a], got {value!r}")
        rgba = list(value) + ([1] if len(value) == 3 else [])
        parts = ", ".join(_float_lit(v) for v in rgba)
        return f"new UnityEngine.Color({parts})"

    if type_name == "string[]":
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError(f"string[] expects a list of strings, got {value!r}")
        items = ", ".join(json.dumps(v, ensure_ascii=False) for v in value)
        return f"new string[] {{ {items} }}"

    if type_name == "int[]":
        if not isinstance(value, list) or not all(
            isinstance(v, int) and not isinstance(v, bool) for v in value
        ):
            raise ValueError(f"int[] expects a list of ints, got {value!r}")
        items = ", ".join(str(v) for v in value)
        return f"new int[] {{ {items} }}"

    if type_name == "float[]":
        if not isinstance(value, list):
            raise ValueError(f"float[] expects a list of numbers, got {value!r}")
        items = ", ".join(_float_lit(v) for v in value)
        return f"new float[] {{ {items} }}"

    raise ValueError(f"unsupported snippet arg type: {type_name!r}")
```

- [ ] **Step 5: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_render -v
```

Expected: 17 tests, all pass.

- [ ] **Step 6: Commit**

```
git add -f cli/snippets/__init__.py cli/snippets/render.py tests/__init__.py tests/test_snippets_render.py
git commit -m "feat(snippets): typed literal renderer for snippet args"
```

(The `-f` is defensive — adjust if `tests/` is not gitignored.)

---

### Task 2: Class wrapper and call generation (`render.py` — submission assembly)

**Files:**
- Modify: `cli/snippets/render.py`
- Modify: `tests/test_snippets_render.py`

- [ ] **Step 1: Append the failing tests**

Append to `tests/test_snippets_render.py`:
```python
from cli.snippets.render import render_submission


SAMPLE_BODY = '''using System.Linq;

static List<string> Run(string layerName) {
    return UnityEngine.Object.FindObjectsOfType<GameObject>()
        .Where(g => LayerMask.LayerToName(g.layer) == layerName)
        .Select(g => g.name).ToList();
}'''


SAMPLE_ARGS_SCHEMA = [
    {"name": "layerName", "type": "string"},
]


class RenderSubmissionTests(unittest.TestCase):
    def test_extracts_using_directive(self):
        text = render_submission(
            snippet_id="scene.find_in_layer",
            body=SAMPLE_BODY,
            args_schema=SAMPLE_ARGS_SCHEMA,
            arg_values={"layerName": "Default"},
        )
        first_line = text.splitlines()[0].strip()
        self.assertEqual(first_line, "using System.Linq;")

    def test_wraps_body_in_unique_class(self):
        text = render_submission(
            snippet_id="scene.find_in_layer",
            body=SAMPLE_BODY,
            args_schema=SAMPLE_ARGS_SCHEMA,
            arg_values={"layerName": "Default"},
        )
        self.assertIn("static class __Snip_", text)
        self.assertIn("static List<string> Run(string layerName)", text)

    def test_call_line_is_last_and_qualified(self):
        text = render_submission(
            snippet_id="scene.find_in_layer",
            body=SAMPLE_BODY,
            args_schema=SAMPLE_ARGS_SCHEMA,
            arg_values={"layerName": "Default"},
        )
        last = text.splitlines()[-1]
        self.assertRegex(last, r'^__Snip_[0-9a-f]{16}\.Run\("Default"\)$')

    def test_hash_stable_across_calls(self):
        a = render_submission(
            snippet_id="x.y", body="static int Run() { return 1; }",
            args_schema=[], arg_values={},
        )
        b = render_submission(
            snippet_id="x.y", body="static int Run() { return 1; }",
            args_schema=[], arg_values={},
        )
        self.assertEqual(_extract_class_name(a), _extract_class_name(b))

    def test_hash_changes_with_body(self):
        a = render_submission(
            snippet_id="x.y", body="static int Run() { return 1; }",
            args_schema=[], arg_values={},
        )
        b = render_submission(
            snippet_id="x.y", body="static int Run() { return 2; }",
            args_schema=[], arg_values={},
        )
        self.assertNotEqual(_extract_class_name(a), _extract_class_name(b))

    def test_default_used_when_arg_missing(self):
        schema = [
            {"name": "layerName", "type": "string"},
            {"name": "limit", "type": "int", "default": 10},
        ]
        body = ("static int Run(string layerName, int limit) "
                "{ return limit; }")
        text = render_submission(
            snippet_id="x.y",
            body=body,
            args_schema=schema,
            arg_values={"layerName": "Default"},
        )
        self.assertIn(".Run(\"Default\", 10)", text)

    def test_missing_required_arg_raises(self):
        with self.assertRaises(ValueError):
            render_submission(
                snippet_id="x.y", body=SAMPLE_BODY,
                args_schema=SAMPLE_ARGS_SCHEMA,
                arg_values={},
            )


def _extract_class_name(text):
    import re
    m = re.search(r"static class (__Snip_[0-9a-f]{16})", text)
    return m.group(1) if m else None
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_render -v
```

Expected: ImportError on `render_submission`.

- [ ] **Step 3: Implement `render_submission`**

Append to `cli/snippets/render.py`:
```python
import hashlib
import re

_USING_RE = re.compile(r"^\s*using\s+[^;]+;\s*$", re.MULTILINE)


def _split_usings(body):
    """Return (using_lines, remaining_body) by extracting top-level usings."""
    usings = _USING_RE.findall(body)
    remaining = _USING_RE.sub("", body).strip("\n")
    return [u.strip() for u in usings], remaining


def _wrapper_class_name(snippet_id, body):
    digest = hashlib.sha1(f"{snippet_id}\n{body}".encode("utf-8")).hexdigest()
    return f"__Snip_{digest[:16]}"


def render_submission(snippet_id, body, args_schema, arg_values):
    """Build the cs exec submission for a single snippet invocation.

    Output shape:

        <usings hoisted from body>
        static class __Snip_<hash16> {
            <body without usings>
        }
        __Snip_<hash16>.Run(<typed-literal>, ...)
    """
    rendered_args = []
    for spec in args_schema:
        name = spec["name"]
        type_name = spec["type"]
        if name in arg_values:
            value = arg_values[name]
        elif "default" in spec:
            value = spec["default"]
        else:
            raise ValueError(f"missing required arg: {name}")
        rendered_args.append(render_literal(type_name, value))

    usings, body_no_usings = _split_usings(body)
    cls = _wrapper_class_name(snippet_id, body)
    parts = []
    for u in usings:
        parts.append(u)
    if usings:
        parts.append("")
    parts.append(f"static class {cls} {{")
    parts.append(body_no_usings)
    parts.append("}")
    parts.append(f"{cls}.Run({', '.join(rendered_args)})")
    return "\n".join(parts)
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_render -v
```

Expected: 24 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/render.py tests/test_snippets_render.py
git commit -m "feat(snippets): wrap body+call in unique static class for symbol isolation"
```

---

### Task 3: Frontmatter parser (`store.py` — schema + parsing)

**Files:**
- Create: `cli/snippets/store.py`
- Create: `tests/test_snippets_store.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_snippets_store.py`:
```python
import unittest

from cli.snippets.store import parse_snippet_file, SnippetParseError


SAMPLE = '''---
id: scene.find_active_in_layer
summary: Find active GameObjects in a specific layer
safety: read-only
args:
  - name: layerName
    type: string
example:
  layerName: "Default"
---

```csharp
using System.Linq;

static List<string> Run(string layerName) {
    return UnityEngine.Object.FindObjectsOfType<GameObject>()
        .Where(g => LayerMask.LayerToName(g.layer) == layerName)
        .Select(g => g.name).ToList();
}
```
'''


class ParseSnippetTests(unittest.TestCase):
    def test_parses_valid_snippet(self):
        snip = parse_snippet_file(SAMPLE)
        self.assertEqual(snip["id"], "scene.find_active_in_layer")
        self.assertEqual(snip["safety"], "read-only")
        self.assertEqual(len(snip["args"]), 1)
        self.assertEqual(snip["args"][0]["name"], "layerName")
        self.assertEqual(snip["args"][0]["type"], "string")
        self.assertEqual(snip["example"], {"layerName": "Default"})
        self.assertIn("static List<string> Run(string layerName)", snip["body"])

    def test_optional_arg_with_default(self):
        text = SAMPLE.replace(
            "  - name: layerName\n    type: string\n",
            "  - name: layerName\n    type: string\n"
            "  - name: limit\n    type: int\n    default: 10\n",
        )
        snip = parse_snippet_file(text)
        self.assertEqual(len(snip["args"]), 2)
        self.assertEqual(snip["args"][1]["default"], 10)

    def test_expected_field_optional(self):
        text = SAMPLE.replace(
            'example:\n  layerName: "Default"\n',
            'example:\n  layerName: "Default"\nexpected: ["A", "B"]\n',
        )
        snip = parse_snippet_file(text)
        self.assertEqual(snip["expected"], ["A", "B"])

    def test_missing_id_raises(self):
        text = SAMPLE.replace("id: scene.find_active_in_layer\n", "")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)

    def test_bad_id_raises(self):
        text = SAMPLE.replace(
            "id: scene.find_active_in_layer", "id: BadID")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)

    def test_unknown_safety_raises(self):
        text = SAMPLE.replace("safety: read-only", "safety: maybe")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)

    def test_missing_csharp_block_raises(self):
        text = SAMPLE.replace("```csharp", "```python")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)

    def test_missing_run_method_raises(self):
        text = SAMPLE.replace("static List<string> Run", "static List<string> Other")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)

    def test_example_missing_required_arg_raises(self):
        text = SAMPLE.replace('example:\n  layerName: "Default"\n', "example: {}\n")
        with self.assertRaises(SnippetParseError):
            parse_snippet_file(text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_store -v
```

Expected: ImportError.

- [ ] **Step 3: Implement the parser**

`cli/snippets/store.py`:
```python
"""Snippet file IO: frontmatter parsing, on-disk layout."""

import json
import re

ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
VALID_SAFETY = {"read-only", "mutates"}
VALID_TYPES = {
    "string", "int", "float", "bool",
    "vector2", "vector3", "vector4", "color",
    "string[]", "int[]", "float[]",
}

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
_CODE_BLOCK_RE = re.compile(r"```csharp\n(.*?)\n```", re.DOTALL)
_RUN_METHOD_RE = re.compile(r"\bstatic\s+[\w<>\[\],\s\.]+?\s+Run\s*\(")


class SnippetParseError(ValueError):
    pass


def _parse_yaml_subset(text):
    """Parse the limited YAML we accept in frontmatter.

    Supports:
      - `key: scalar`
      - `key: [..]` / `key: {..}` (parsed as JSON)
      - `key:` followed by indented `- name: ...` blocks (lists of dicts)
      - `key:` followed by indented `subkey: value` blocks (mappings)
    """
    out = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if not line.lstrip().startswith("- "):
            if ":" not in line:
                raise SnippetParseError(f"malformed frontmatter line: {line!r}")
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not rest:
                block_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    block_lines.append(lines[i])
                    i += 1
                out[key] = _parse_block(block_lines)
                continue
            out[key] = _parse_scalar_or_inline(rest)
        else:
            raise SnippetParseError(f"top-level list not allowed: {line!r}")
        i += 1
    return out


def _parse_block(block_lines):
    stripped = [ln for ln in block_lines if ln.strip()]
    if not stripped:
        return {}
    first = stripped[0].lstrip()
    if first.startswith("- "):
        return _parse_list_of_dicts(stripped)
    return _parse_mapping_block(stripped)


def _parse_list_of_dicts(lines):
    items = []
    current = None
    for ln in lines:
        s = ln.lstrip()
        if s.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            s = s[2:]
            if ":" in s:
                k, _, v = s.partition(":")
                current[k.strip()] = _parse_scalar_or_inline(v.strip())
        else:
            if current is None:
                raise SnippetParseError(f"unexpected indent: {ln!r}")
            if ":" not in s:
                raise SnippetParseError(f"malformed list item line: {ln!r}")
            k, _, v = s.partition(":")
            current[k.strip()] = _parse_scalar_or_inline(v.strip())
    if current is not None:
        items.append(current)
    return items


def _parse_mapping_block(lines):
    out = {}
    for ln in lines:
        s = ln.strip()
        if ":" not in s:
            raise SnippetParseError(f"malformed mapping line: {ln!r}")
        k, _, v = s.partition(":")
        out[k.strip()] = _parse_scalar_or_inline(v.strip())
    return out


def _parse_scalar_or_inline(text):
    if text == "":
        return None
    if text.startswith("[") or text.startswith("{") or text.startswith('"'):
        return json.loads(text)
    if text in ("true", "false"):
        return text == "true"
    if text in ("null", "~"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _validate(snip):
    for required in ("id", "summary", "safety", "args", "example"):
        if required not in snip:
            raise SnippetParseError(f"frontmatter missing required field: {required}")
    if not ID_RE.match(snip["id"]):
        raise SnippetParseError(f"invalid id: {snip['id']!r}")
    if snip["safety"] not in VALID_SAFETY:
        raise SnippetParseError(
            f"unknown safety class: {snip['safety']!r} "
            f"(must be one of {sorted(VALID_SAFETY)})"
        )
    if not isinstance(snip["args"], list):
        raise SnippetParseError("args must be a list")
    seen_names = set()
    for spec in snip["args"]:
        for k in ("name", "type"):
            if k not in spec:
                raise SnippetParseError(f"arg missing {k}: {spec!r}")
        if spec["type"] not in VALID_TYPES:
            raise SnippetParseError(
                f"arg {spec['name']!r}: unknown type {spec['type']!r}"
            )
        if spec["name"] in seen_names:
            raise SnippetParseError(f"duplicate arg name: {spec['name']!r}")
        seen_names.add(spec["name"])
    if not isinstance(snip["example"], dict):
        raise SnippetParseError("example must be a mapping")
    for spec in snip["args"]:
        if "default" not in spec and spec["name"] not in snip["example"]:
            raise SnippetParseError(
                f"example missing required arg: {spec['name']!r}"
            )


def parse_snippet_file(text):
    """Parse a snippet markdown file's full contents.

    Returns a dict with keys: id, summary, safety, args, example,
    expected (optional), body. Raises SnippetParseError on any issue.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise SnippetParseError("missing frontmatter (--- ... ---) block")
    fm_text, after = m.group(1), m.group(2)
    snip = _parse_yaml_subset(fm_text)
    _validate(snip)
    code_match = _CODE_BLOCK_RE.search(after)
    if not code_match:
        raise SnippetParseError("missing ```csharp code block")
    body = code_match.group(1).strip("\n")
    if not _RUN_METHOD_RE.search(body):
        raise SnippetParseError("snippet body must declare a `static Run(...)` method")
    snip["body"] = body
    return snip
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_store -v
```

Expected: 9 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/store.py tests/test_snippets_store.py
git commit -m "feat(snippets): frontmatter parser with schema validation"
```

---

### Task 4: Snippet file storage IO (`store.py` — paths and round-trip)

**Files:**
- Modify: `cli/snippets/store.py`
- Modify: `tests/test_snippets_store.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_snippets_store.py`:
```python
import tempfile
from pathlib import Path

from cli.snippets.store import (
    snippets_dir, snippet_path,
    write_snippet_file, read_snippet_file, list_snippet_ids,
)


class StorageIOTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_snippets_dir_uses_tilde(self):
        d = snippets_dir(self.root)
        self.assertTrue(d.name.endswith("snippets~"))
        self.assertEqual(d.parent.name, ".unity-cli")

    def test_snippet_path_for_id(self):
        p = snippet_path(self.root, "scene.find_active_in_layer")
        self.assertEqual(p.name, "scene.find_active_in_layer.md")
        self.assertEqual(p.parent, snippets_dir(self.root))

    def test_write_then_read(self):
        write_snippet_file(self.root, "scene.find_active_in_layer", SAMPLE)
        text = read_snippet_file(self.root, "scene.find_active_in_layer")
        self.assertEqual(text, SAMPLE)

    def test_read_missing_returns_none(self):
        self.assertIsNone(read_snippet_file(self.root, "no.such.snippet"))

    def test_list_ids_alphabetical(self):
        write_snippet_file(self.root, "b.x", SAMPLE.replace("scene.find_active_in_layer", "b.x"))
        write_snippet_file(self.root, "a.y", SAMPLE.replace("scene.find_active_in_layer", "a.y"))
        ids = list_snippet_ids(self.root)
        self.assertEqual(ids, ["a.y", "b.x"])

    def test_list_ids_empty_when_dir_missing(self):
        self.assertEqual(list_snippet_ids(self.root), [])
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_store -v
```

Expected: ImportError on the new functions.

- [ ] **Step 3: Implement the storage helpers**

Append to `cli/snippets/store.py`:
```python
from pathlib import Path

DATA_DIR_NAME = ".unity-cli"
SNIPPETS_SUBDIR = "snippets~"


def snippets_dir(project_root):
    return Path(project_root) / DATA_DIR_NAME / SNIPPETS_SUBDIR


def snippet_path(project_root, snippet_id):
    return snippets_dir(project_root) / f"{snippet_id}.md"


def write_snippet_file(project_root, snippet_id, text):
    p = snippet_path(project_root, snippet_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def read_snippet_file(project_root, snippet_id):
    p = snippet_path(project_root, snippet_id)
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8")


def list_snippet_ids(project_root):
    d = snippets_dir(project_root)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.md"))
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_store -v
```

Expected: 15 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/store.py tests/test_snippets_store.py
git commit -m "feat(snippets): file IO helpers for snippet bodies"
```

---

### Task 5: Audit and stats IO (`stats.py`)

**Files:**
- Create: `cli/snippets/stats.py`
- Create: `tests/test_snippets_stats.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_snippets_stats.py`:
```python
import tempfile
import unittest
from pathlib import Path

from cli.snippets.stats import (
    audit_path, stats_path,
    load_audit, save_audit, init_audit_entry, mark_deprecated,
    load_stats, init_stats_entry,
    record_success, record_failure,
)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_paths_under_unity_cli(self):
        self.assertEqual(audit_path(self.root).name, "snippets-audit.json")
        self.assertEqual(audit_path(self.root).parent.name, ".unity-cli")
        self.assertEqual(stats_path(self.root).name, "snippets-stats.json")

    def test_init_audit_entry(self):
        init_audit_entry(self.root, "scene.x", verified=True, when="2026-05-07T00:00:00Z")
        audit = load_audit(self.root)
        e = audit["snippets"]["scene.x"]
        self.assertEqual(e["created_at"], "2026-05-07T00:00:00Z")
        self.assertEqual(e["verified_at"], "2026-05-07T00:00:00Z")
        self.assertFalse(e["unverified"])
        self.assertFalse(e["deprecated"])

    def test_init_audit_entry_unverified(self):
        init_audit_entry(self.root, "scene.x", verified=False, when="2026-05-07T00:00:00Z")
        e = load_audit(self.root)["snippets"]["scene.x"]
        self.assertTrue(e["unverified"])
        self.assertIsNone(e["verified_at"])

    def test_mark_deprecated(self):
        init_audit_entry(self.root, "scene.x", verified=True, when="2026-05-07T00:00:00Z")
        mark_deprecated(self.root, "scene.x",
                        reason="superseded", supersede="scene.y",
                        when="2026-06-01T00:00:00Z")
        e = load_audit(self.root)["snippets"]["scene.x"]
        self.assertTrue(e["deprecated"])
        self.assertEqual(e["deprecated_reason"], "superseded")
        self.assertEqual(e["supersedes"], "scene.y")
        self.assertEqual(e["deprecated_at"], "2026-06-01T00:00:00Z")


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_stats_entry_uses_created_at_for_last_used(self):
        init_stats_entry(self.root, "scene.x", created_at="2026-05-07T00:00:00Z")
        e = load_stats(self.root)["snippets"]["scene.x"]
        self.assertEqual(e["successes"], 0)
        self.assertEqual(e["failures"], 0)
        self.assertEqual(e["last_used"], "2026-05-07T00:00:00Z")
        self.assertIsNone(e["last_failure"])
        self.assertIsNone(e["first_failure_in_streak"])
        self.assertEqual(e["consecutive_failures"], 0)

    def test_record_success_clears_streak(self):
        init_stats_entry(self.root, "scene.x", created_at="2026-05-07T00:00:00Z")
        record_failure(self.root, "scene.x", when="2026-05-08T00:00:00Z")
        record_failure(self.root, "scene.x", when="2026-05-09T00:00:00Z")
        record_success(self.root, "scene.x", when="2026-05-10T00:00:00Z")
        e = load_stats(self.root)["snippets"]["scene.x"]
        self.assertEqual(e["successes"], 1)
        self.assertEqual(e["failures"], 2)
        self.assertEqual(e["consecutive_failures"], 0)
        self.assertIsNone(e["first_failure_in_streak"])
        self.assertEqual(e["last_used"], "2026-05-10T00:00:00Z")

    def test_record_failure_tracks_streak_window(self):
        init_stats_entry(self.root, "scene.x", created_at="2026-05-07T00:00:00Z")
        record_failure(self.root, "scene.x", when="2026-05-08T00:00:00Z")
        record_failure(self.root, "scene.x", when="2026-05-15T00:00:00Z")
        e = load_stats(self.root)["snippets"]["scene.x"]
        self.assertEqual(e["consecutive_failures"], 2)
        self.assertEqual(e["first_failure_in_streak"], "2026-05-08T00:00:00Z")
        self.assertEqual(e["last_failure"], "2026-05-15T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_stats -v
```

Expected: ImportError.

- [ ] **Step 3: Implement stats and audit IO**

`cli/snippets/stats.py`:
```python
"""Audit and stats persistence for snippets."""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR_NAME = ".unity-cli"
AUDIT_FILE = "snippets-audit.json"
STATS_FILE = "snippets-stats.json"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit_path(project_root):
    return Path(project_root) / DATA_DIR_NAME / AUDIT_FILE


def stats_path(project_root):
    return Path(project_root) / DATA_DIR_NAME / STATS_FILE


def _load_json(path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")


def load_audit(project_root):
    return _load_json(audit_path(project_root), {"version": 1, "snippets": {}})


def save_audit(project_root, data):
    _save_json(audit_path(project_root), data)


def init_audit_entry(project_root, snippet_id, *, verified, when=None):
    when = when or _now()
    audit = load_audit(project_root)
    audit["snippets"][snippet_id] = {
        "created_at": when,
        "verified_at": when if verified else None,
        "unverified": not verified,
        "deprecated": False,
        "deprecated_at": None,
        "deprecated_reason": None,
        "supersedes": None,
    }
    save_audit(project_root, audit)


def mark_deprecated(project_root, snippet_id, *, reason=None, supersede=None, when=None):
    when = when or _now()
    audit = load_audit(project_root)
    if snippet_id not in audit["snippets"]:
        raise KeyError(snippet_id)
    e = audit["snippets"][snippet_id]
    e["deprecated"] = True
    e["deprecated_at"] = when
    e["deprecated_reason"] = reason
    e["supersedes"] = supersede
    save_audit(project_root, audit)


def load_stats(project_root):
    return _load_json(stats_path(project_root), {"version": 1, "snippets": {}})


def save_stats(project_root, data):
    _save_json(stats_path(project_root), data)


def init_stats_entry(project_root, snippet_id, *, created_at):
    stats = load_stats(project_root)
    stats["snippets"][snippet_id] = {
        "successes": 0,
        "failures": 0,
        "last_used": created_at,
        "last_failure": None,
        "first_failure_in_streak": None,
        "consecutive_failures": 0,
    }
    save_stats(project_root, stats)


def _ensure_entry(stats, snippet_id, when):
    return stats["snippets"].setdefault(snippet_id, {
        "successes": 0, "failures": 0, "last_used": when,
        "last_failure": None, "first_failure_in_streak": None,
        "consecutive_failures": 0,
    })


def record_success(project_root, snippet_id, *, when=None):
    when = when or _now()
    stats = load_stats(project_root)
    e = _ensure_entry(stats, snippet_id, when)
    e["successes"] += 1
    e["last_used"] = when
    e["consecutive_failures"] = 0
    e["first_failure_in_streak"] = None
    save_stats(project_root, stats)


def record_failure(project_root, snippet_id, *, when=None):
    when = when or _now()
    stats = load_stats(project_root)
    e = _ensure_entry(stats, snippet_id, when)
    e["failures"] += 1
    e["last_used"] = when
    e["last_failure"] = when
    if e["consecutive_failures"] == 0:
        e["first_failure_in_streak"] = when
    e["consecutive_failures"] += 1
    save_stats(project_root, stats)
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_stats -v
```

Expected: 7 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/stats.py tests/test_snippets_stats.py
git commit -m "feat(snippets): audit and stats IO with success/failure tracking"
```

---

### Task 6: Validation gate for `read-only` (`validate.py`)

**Files:**
- Create: `cli/snippets/validate.py`
- Create: `tests/test_snippets_validate.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_snippets_validate.py`:
```python
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


def _ok_response(payload="[\"Default\"]"):
    return {"ok": True, "exitCode": 0, "data": {"resultJson": payload}}


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
        snip = dict(SAMPLE_SNIPPET, expected=["Default"])
        def fake_runner(code):
            return _ok_response('["Default"]')
        validate_snippet(snip, fake_runner)

    def test_expected_mismatch_fails(self):
        snip = dict(SAMPLE_SNIPPET, expected=["Default"])
        def fake_runner(code):
            return _ok_response('["Other"]')
        with self.assertRaises(ValidationError) as ctx:
            validate_snippet(snip, fake_runner)
        self.assertIn("expected", str(ctx.exception).lower())

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_validate -v
```

Expected: ImportError.

- [ ] **Step 3: Implement the validation gate**

`cli/snippets/validate.py`:
```python
"""Snippet validation: smoke-test runs example through a code runner."""

import json

from cli.snippets.render import render_submission


class ValidationError(Exception):
    pass


def _extract_return_value(response):
    """Pull the REPL's last-expression result out of a session response.

    csharpconsole returns either ``data.resultJson`` (string-encoded JSON) for
    serializable values, or omits it for void / unsupported. Caller should
    handle None.
    """
    data = response.get("data") or {}
    rj = data.get("resultJson")
    if rj is None:
        return None
    if isinstance(rj, str):
        try:
            return json.loads(rj)
        except (ValueError, TypeError):
            return rj
    return rj


def validate_snippet(snippet, code_runner, no_validate=False):
    """Validate a parsed snippet by running its example through *code_runner*.

    *code_runner* signature: ``code_runner(code: str) -> dict`` (matches the
    ConsoleSession `exec` return shape).

    Raises ValidationError on any failure.

    For ``safety == 'mutates'`` snippets, validation is refused unless
    *no_validate* is True.
    """
    if snippet["safety"] == "mutates":
        if not no_validate:
            raise ValidationError(
                "snippet has safety=mutates and cannot be auto-validated; "
                "pass --no-validate to register it as unverified"
            )
        return  # skipped, caller marks unverified in audit

    if no_validate:
        return  # explicit skip even for read-only

    submission = render_submission(
        snippet_id=snippet["id"],
        body=snippet["body"],
        args_schema=snippet["args"],
        arg_values=snippet["example"],
    )
    response = code_runner(submission)
    if not response.get("ok") or response.get("exitCode", 0) != 0:
        msg = response.get("summary") or response.get("error") or "validation runner failed"
        raise ValidationError(f"validation failed: {msg}")

    if "expected" in snippet and snippet["expected"] is not None:
        actual = _extract_return_value(response)
        if actual != snippet["expected"]:
            raise ValidationError(
                f"expected mismatch: got {actual!r}, want {snippet['expected']!r}"
            )
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_validate -v
```

Expected: 6 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/validate.py tests/test_snippets_validate.py
git commit -m "feat(snippets): validation gate (read-only auto, mutates refused)"
```

---

### Task 7: CLI parser + `cs snippets add`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the snippets subparser block in `main()`**

Find the catalog subparser block in `cli/cs.py` (around line 930). Append immediately after it:

```python
    sp_sn = sub.add_parser("snippets", parents=[shared], help="Reusable C# snippet library")
    sn_sub = sp_sn.add_subparsers(dest="snippets_cmd")

    sp_sn_add = sn_sub.add_parser("add", parents=[shared], help="Validate and register a snippet")
    sp_sn_add.add_argument("snippet_id", help="Snippet id (dotted, e.g. scene.find_in_layer)")
    sp_sn_add.add_argument("--file", "-f", dest="file", required=True,
                           help="Path to the snippet markdown file")
    sp_sn_add.add_argument("--no-validate", dest="no_validate", action="store_true",
                           help="Skip validation gate; register as unverified (required for mutates)")

    sp_sn_use = sn_sub.add_parser("use", parents=[shared], help="Run a snippet")
    sp_sn_use.add_argument("snippet_id")
    sp_sn_use.add_argument("--args", dest="snippet_args", default=None,
                           help="JSON object of arg values")
    sp_sn_use.add_argument("--dry-run", dest="dry_run", action="store_true",
                           help="Print the wrapped submission without executing")

    sp_sn_list = sn_sub.add_parser("list", parents=[shared], help="List snippets")
    sp_sn_list.add_argument("--include-deprecated", dest="include_deprecated",
                            action="store_true")
    sp_sn_list.add_argument("--safety", choices=["read-only", "mutates"], default=None)
    sp_sn_list.add_argument("--sort", choices=["hot", "cold", "recent"], default=None)

    sp_sn_show = sn_sub.add_parser("show", parents=[shared],
                                    help="Show a snippet body and metadata")
    sp_sn_show.add_argument("snippet_id")
```

- [ ] **Step 2: Add the dispatch block**

Find the catalog dispatch block in `main()` (around line 1000). Append immediately after it:

```python
    if args.cmd == "snippets":
        if root is None:
            print("Error: no Unity project found.", file=sys.stderr)
            sys.exit(1)
        if args.snippets_cmd == "add":
            sys.exit(cmd_snippets_add(root, args, agent_root))
        elif args.snippets_cmd == "use":
            sys.exit(cmd_snippets_use(root, args, agent_root))
        elif args.snippets_cmd == "list":
            sys.exit(cmd_snippets_list(root, args))
        elif args.snippets_cmd == "show":
            sys.exit(cmd_snippets_show(root, args))
        else:
            sp_sn.print_help()
            sys.exit(1)
```

- [ ] **Step 3: Add the `_print_envelope` helper and `cmd_snippets_add`**

Add these functions in `cli/cs.py` alongside other `cmd_*` functions, before `main()`:

```python
def _print_envelope(result, as_json):
    if as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        if result.get("ok"):
            print(result.get("summary", "OK"))
        else:
            print(f"Error: {result.get('summary', 'failed')}", file=sys.stderr)


def cmd_snippets_add(root, args, agent_root):
    from cli.snippets.store import (parse_snippet_file, write_snippet_file,
                                    SnippetParseError)
    from cli.snippets.validate import validate_snippet, ValidationError
    from cli.snippets.stats import init_audit_entry, init_stats_entry, load_audit
    from cli.core_bridge import find_package_dir

    try:
        text = Path(args.file).read_text(encoding="utf-8-sig")
    except OSError as e:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": f"cannot read --file: {e}"},
            args.as_json,
        )
        return 1

    try:
        snip = parse_snippet_file(text)
    except SnippetParseError as e:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": f"parse error: {e}"},
            args.as_json,
        )
        return 1

    if snip["id"] != args.snippet_id:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"id mismatch: file declares {snip['id']!r}, "
                        f"CLI got {args.snippet_id!r}"},
            args.as_json,
        )
        return 1

    audit = load_audit(root)
    if args.snippet_id in audit["snippets"]:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"snippet {args.snippet_id!r} already exists; "
                        f"use `cs snippets update`"},
            args.as_json,
        )
        return 1

    pkg_dir = find_package_dir(root, agent_root) if not args.no_validate else None
    if pkg_dir is None and not args.no_validate:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": "package not found and --no-validate not set"},
            args.as_json,
        )
        return 1

    code_runner = None
    if pkg_dir is not None:
        session = _new_session(root, args, pkg_dir)
        code_runner = session.exec

    try:
        validate_snippet(
            snip,
            code_runner or (lambda code: {"ok": False, "summary": "no runner"}),
            no_validate=args.no_validate,
        )
    except ValidationError as e:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": f"validation failed: {e}"},
            args.as_json,
        )
        return 1

    write_snippet_file(root, args.snippet_id, text)
    init_audit_entry(root, args.snippet_id, verified=not args.no_validate)
    audit_after = load_audit(root)
    created_at = audit_after["snippets"][args.snippet_id]["created_at"]
    init_stats_entry(root, args.snippet_id, created_at=created_at)

    _print_envelope(
        {"ok": True, "exitCode": 0,
         "summary": f"registered {args.snippet_id}"
                    + (" (unverified)" if args.no_validate else "")},
        args.as_json,
    )
    return 0
```

- [ ] **Step 4: Add stub implementations for use/list/show**

Stubs so the dispatch compiles; replaced in Tasks 8 and 9:

```python
def cmd_snippets_use(root, args, agent_root):
    print("not yet implemented", file=sys.stderr)
    return 2


def cmd_snippets_list(root, args):
    print("not yet implemented", file=sys.stderr)
    return 2


def cmd_snippets_show(root, args):
    print("not yet implemented", file=sys.stderr)
    return 2
```

- [ ] **Step 5: Smoke-test `add` against a Unity project**

In a Unity project with the `com.zh1zh1.csharpconsole` package installed and the editor open, create `/tmp/test_snippet.md`:

````markdown
---
id: scene.list_root_objects
summary: List the names of all root GameObjects in the active scene
safety: read-only
args: []
example: {}
---

```csharp
using System.Linq;
using UnityEngine.SceneManagement;

static List<string> Run() {
    return SceneManager.GetActiveScene().GetRootGameObjects()
        .Select(g => g.name).ToList();
}
```
````

Run:
```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets add scene.list_root_objects --file /tmp/test_snippet.md --json
```

Expected: `{"ok": true, "summary": "registered scene.list_root_objects"}`. Verify the snippet appears at `<project>/.unity-cli/snippets~/scene.list_root_objects.md` and the audit/stats files have entries.

- [ ] **Step 6: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets parser + add subcommand"
```

---

### Task 8: `cs snippets use`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Replace the `cmd_snippets_use` stub**

Replace the stub from Task 7:

```python
def cmd_snippets_use(root, args, agent_root):
    from cli.snippets.store import read_snippet_file, parse_snippet_file
    from cli.snippets.render import render_submission
    from cli.snippets.stats import load_audit, record_success, record_failure
    from cli.core_bridge import find_package_dir

    text = read_snippet_file(root, args.snippet_id)
    if text is None:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"snippet not found: {args.snippet_id}"},
            args.as_json,
        )
        return 1

    snip = parse_snippet_file(text)

    audit = load_audit(root)
    audit_entry = audit["snippets"].get(args.snippet_id)
    if audit_entry and audit_entry.get("deprecated"):
        reason = audit_entry.get("deprecated_reason")
        suffix = f" ({reason})" if reason else ""
        print(f"warning: snippet {args.snippet_id!r} is deprecated{suffix}",
              file=sys.stderr)

    arg_values = {}
    if args.snippet_args:
        try:
            arg_values = json.loads(args.snippet_args)
        except json.JSONDecodeError as e:
            _print_envelope(
                {"ok": False, "exitCode": 1,
                 "summary": f"--args is not valid JSON: {e}"},
                args.as_json,
            )
            return 1
        if not isinstance(arg_values, dict):
            _print_envelope(
                {"ok": False, "exitCode": 1,
                 "summary": "--args must decode to a JSON object"},
                args.as_json,
            )
            return 1

    try:
        submission = render_submission(
            snippet_id=snip["id"],
            body=snip["body"],
            args_schema=snip["args"],
            arg_values=arg_values,
        )
    except ValueError as e:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": f"arg error: {e}"},
            args.as_json,
        )
        return 1

    if args.dry_run:
        _print_envelope(
            {"ok": True, "exitCode": 0, "summary": "dry run",
             "data": {"submission": submission}},
            args.as_json,
        )
        return 0

    pkg_dir = find_package_dir(root, agent_root)
    if pkg_dir is None:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": "package not found"},
            args.as_json,
        )
        return 1
    session = _new_session(root, args, pkg_dir)
    code_runner = session.exec
    response = code_runner(submission)

    if response.get("ok") and response.get("exitCode", 0) == 0:
        record_success(root, args.snippet_id)
    else:
        record_failure(root, args.snippet_id)

    if args.as_json:
        json.dump(response, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        session.emit(response)
    return response.get("exitCode", 0)
```

- [ ] **Step 2: Smoke-test `use`**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets use scene.list_root_objects --json
```

Expected: returns `ok=true` with the list of root GameObject names in the response payload.

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets use scene.list_root_objects --dry-run --json
```

Expected: prints the wrapped submission, does NOT execute.

Verify stats updated:
```
cat <project>/.unity-cli/snippets-stats.json
```

Expected: `successes: 1`, `last_used` recent, `consecutive_failures: 0`.

- [ ] **Step 3: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets use with stats tracking"
```

---

### Task 9: `cs snippets list` and `show`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Replace the stubs**

Replace the `cmd_snippets_list` and `cmd_snippets_show` stubs:

```python
def cmd_snippets_list(root, args):
    from cli.snippets.store import (list_snippet_ids, read_snippet_file,
                                    parse_snippet_file)
    from cli.snippets.stats import load_audit, load_stats

    ids = list_snippet_ids(root)
    audit = load_audit(root)
    stats = load_stats(root)
    rows = []
    for sid in ids:
        a = audit["snippets"].get(sid, {})
        if a.get("deprecated") and not args.include_deprecated:
            continue
        text = read_snippet_file(root, sid) or ""
        try:
            snip = parse_snippet_file(text)
        except Exception:
            continue
        if args.safety and snip["safety"] != args.safety:
            continue
        st = stats["snippets"].get(sid, {})
        rows.append({
            "id": sid,
            "summary": snip["summary"],
            "safety": snip["safety"],
            "deprecated": a.get("deprecated", False),
            "unverified": a.get("unverified", False),
            "successes": st.get("successes", 0),
            "failures": st.get("failures", 0),
            "last_used": st.get("last_used"),
        })

    if args.sort == "hot":
        rows.sort(key=lambda r: -r["successes"])
    elif args.sort == "recent":
        rows.sort(key=lambda r: r["last_used"] or "", reverse=True)
    elif args.sort == "cold":
        rows.sort(key=lambda r: (r["successes"], r["last_used"] or ""))

    result = {
        "ok": True, "exitCode": 0,
        "summary": f"{len(rows)} snippet(s)",
        "data": {"snippets": rows},
    }
    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(result["summary"])
        for r in rows:
            tags = []
            if r["unverified"]:
                tags.append("⚠unverified")
            if r["deprecated"]:
                tags.append("DEPRECATED")
            tag_s = f" [{', '.join(tags)}]" if tags else ""
            print(f"  {r['id']} ({r['safety']}){tag_s} — {r['summary']}")
    return 0


def cmd_snippets_show(root, args):
    from cli.snippets.store import read_snippet_file, parse_snippet_file
    from cli.snippets.stats import load_audit, load_stats

    text = read_snippet_file(root, args.snippet_id)
    if text is None:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"snippet not found: {args.snippet_id}"},
            args.as_json,
        )
        return 1
    try:
        snip = parse_snippet_file(text)
    except Exception as e:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": f"parse error: {e}"},
            args.as_json,
        )
        return 1
    audit = load_audit(root)["snippets"].get(args.snippet_id, {})
    stats = load_stats(root)["snippets"].get(args.snippet_id, {})

    if args.as_json:
        json.dump({
            "ok": True, "exitCode": 0,
            "data": {
                "id": snip["id"], "summary": snip["summary"],
                "safety": snip["safety"], "args": snip["args"],
                "example": snip["example"],
                "expected": snip.get("expected"),
                "body": snip["body"],
                "audit": audit, "stats": stats,
            },
        }, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(f"{snip['id']} ({snip['safety']}) — {snip['summary']}")
        print()
        print("Args:")
        for spec in snip["args"]:
            default = f" = {spec['default']!r}" if "default" in spec else ""
            print(f"  {spec['name']}: {spec['type']}{default}")
        print()
        print("Example:", snip["example"])
        if snip.get("expected") is not None:
            print("Expected:", snip["expected"])
        print()
        print("Body:")
        print(snip["body"])
    return 0
```

- [ ] **Step 2: Smoke-test list and show**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets list --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets show scene.list_root_objects --json
```

Expected: `list` returns the registered snippet; `show` returns full body+audit+stats.

- [ ] **Step 3: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets list and show"
```

---

### Task 10: D0 end-to-end smoke test

**Files:**
- Create: `docs/superpowers/notes/2026-05-07-d0-smoke-results.md`

- [ ] **Step 1: Set up a clean run in a real Unity project**

In a Unity project with the `com.zh1zh1.csharpconsole` package installed and the editor open:

```
rm -rf <project>/.unity-cli/snippets~ <project>/.unity-cli/snippets-audit.json <project>/.unity-cli/snippets-stats.json
```

- [ ] **Step 2: Add a `read-only` snippet with `expected`**

Create `/tmp/snip_query.md`:

````markdown
---
id: scene.count_root_objects
summary: Count root GameObjects in the active scene
safety: read-only
args: []
example: {}
---

```csharp
using UnityEngine.SceneManagement;

static int Run() {
    return SceneManager.GetActiveScene().GetRootGameObjects().Length;
}
```
````

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets add scene.count_root_objects --file /tmp/snip_query.md --json
```

Expected: `ok=true`, `summary: "registered scene.count_root_objects"`.

- [ ] **Step 3: Use the snippet**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets use scene.count_root_objects --json
```

Expected: `ok=true`, response payload contains the integer count.

- [ ] **Step 4: Add a `mutates` snippet (refused without --no-validate)**

Create `/tmp/snip_create.md`:

````markdown
---
id: scene.create_marker
summary: Create an empty marker GameObject
safety: mutates
args:
  - name: name
    type: string
example:
  name: "Marker"
---

```csharp
static void Run(string name) {
    var go = new GameObject(name);
}
```
````

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets add scene.create_marker --file /tmp/snip_create.md --json
```

Expected: `ok=false`, summary mentions "safety=mutates" and `--no-validate`.

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets add scene.create_marker --file /tmp/snip_create.md --no-validate --json
```

Expected: `ok=true`, audit entry has `unverified: true`.

- [ ] **Step 5: List shows both, show one, use the marker**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets list --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets show scene.create_marker --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets use scene.create_marker --args '{"name":"M1"}' --json
```

Expected: list returns 2 entries, the mutates one prefixed `⚠`. `use` of marker creates an "M1" GameObject in the active scene.

- [ ] **Step 6: Capture results and commit**

Save the actual JSON outputs of every step into `docs/superpowers/notes/2026-05-07-d0-smoke-results.md`. This is the proof-of-architecture artifact for D0.

```
git add -f docs/superpowers/notes/2026-05-07-d0-smoke-results.md
git commit -m "docs(snippets): D0 end-to-end smoke test results"
```

D0 is now shippable — the wrap-and-validate-and-execute loop is proven on the smallest possible surface.

---

## Phase D1 — Full CLI Surface

### Task 11: `cs snippets search`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the `search` subparser**

Inside the `snippets` subparser block in `main()`, append after the `show` subparser:

```python
    sp_sn_search = sn_sub.add_parser("search", parents=[shared],
                                      help="Search snippet library")
    sp_sn_search.add_argument("query", help="Free-text query")
    sp_sn_search.add_argument("--top", type=int, default=5)
```

- [ ] **Step 2: Add to dispatch**

Inside the `snippets` dispatch block:

```python
        elif args.snippets_cmd == "search":
            sys.exit(cmd_snippets_search(root, args))
```

- [ ] **Step 3: Implement `cmd_snippets_search`**

```python
def cmd_snippets_search(root, args):
    from cli.snippets.store import (list_snippet_ids, read_snippet_file,
                                    parse_snippet_file)
    from cli.snippets.stats import load_audit

    audit = load_audit(root)
    q = args.query.lower()
    q_terms = [t for t in q.split() if t]
    hits = []
    for sid in list_snippet_ids(root):
        a = audit["snippets"].get(sid, {})
        if a.get("deprecated"):
            continue
        text = read_snippet_file(root, sid) or ""
        try:
            snip = parse_snippet_file(text)
        except Exception:
            continue
        haystack = f"{sid} {snip['summary']}".lower()
        score = sum(1 for t in q_terms if t in haystack)
        if score > 0:
            hits.append((score, sid, snip))
    hits.sort(key=lambda x: (-x[0], x[1]))
    top = hits[: args.top]
    rows = []
    for score, sid, snip in top:
        args_summary = ", ".join(
            f"{a['name']}:{a['type']}" for a in snip["args"]
        )
        rows.append({
            "id": sid, "summary": snip["summary"],
            "args": args_summary, "score": score,
        })
    result = {
        "ok": True, "exitCode": 0,
        "summary": f"{len(rows)} hit(s) for {args.query!r}",
        "data": {"results": rows},
    }
    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(result["summary"])
        for r in rows:
            print(f"  {r['id']}({r['args']}) — {r['summary']}")
    return 0
```

- [ ] **Step 4: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets search "root scene" --json
```

Expected: hits include `scene.count_root_objects` and `scene.list_root_objects`.

- [ ] **Step 5: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets search (lexical, top-N)"
```

---

### Task 12: `cs snippets update` (--file and --set)

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the `update` subparser**

Inside the `snippets` subparser block, append:

```python
    sp_sn_update = sn_sub.add_parser("update", parents=[shared],
                                      help="Update an existing snippet")
    sp_sn_update.add_argument("snippet_id")
    sp_sn_update.add_argument("--file", "-f", dest="file", default=None,
                              help="Replace the snippet body (re-runs validation gate)")
    sp_sn_update.add_argument("--set", dest="set_field", action="append", default=[],
                              metavar="key=value",
                              help="Update a metadata-only field (summary or arg description). "
                                   "Repeat for multiple. Cannot change args/example/safety/expected/body.")
    sp_sn_update.add_argument("--no-validate", dest="no_validate", action="store_true")
```

- [ ] **Step 2: Add to dispatch**

```python
        elif args.snippets_cmd == "update":
            sys.exit(cmd_snippets_update(root, args, agent_root))
```

- [ ] **Step 3: Implement `cmd_snippets_update`**

```python
def cmd_snippets_update(root, args, agent_root):
    from cli.snippets.store import (read_snippet_file, parse_snippet_file,
                                    write_snippet_file, SnippetParseError)
    from cli.snippets.validate import validate_snippet, ValidationError
    from cli.snippets.stats import load_audit, save_audit, _now
    from cli.core_bridge import find_package_dir

    if not args.file and not args.set_field:
        _print_envelope(
            {"ok": False, "exitCode": 1, "summary": "must pass --file or --set"},
            args.as_json,
        )
        return 1

    existing = read_snippet_file(root, args.snippet_id)
    if existing is None:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"snippet not found: {args.snippet_id}"},
            args.as_json,
        )
        return 1

    if args.file:
        try:
            new_text = Path(args.file).read_text(encoding="utf-8-sig")
        except OSError as e:
            _print_envelope(
                {"ok": False, "exitCode": 1, "summary": f"cannot read --file: {e}"},
                args.as_json,
            )
            return 1
        try:
            new_snip = parse_snippet_file(new_text)
        except SnippetParseError as e:
            _print_envelope(
                {"ok": False, "exitCode": 1, "summary": f"parse error: {e}"},
                args.as_json,
            )
            return 1
        if new_snip["id"] != args.snippet_id:
            _print_envelope(
                {"ok": False, "exitCode": 1,
                 "summary": "id mismatch between --file and CLI argument"},
                args.as_json,
            )
            return 1

        pkg_dir = find_package_dir(root, agent_root) if not args.no_validate else None
        if pkg_dir is not None:
            session = _new_session(root, args, pkg_dir)
            code_runner = session.exec
        else:
            code_runner = lambda c: {"ok": False, "summary": "no runner"}
        try:
            validate_snippet(new_snip, code_runner, no_validate=args.no_validate)
        except ValidationError as e:
            _print_envelope(
                {"ok": False, "exitCode": 1, "summary": f"validation failed: {e}"},
                args.as_json,
            )
            return 1
        write_snippet_file(root, args.snippet_id, new_text)

        audit = load_audit(root)
        e = audit["snippets"][args.snippet_id]
        if not args.no_validate:
            e["verified_at"] = _now()
            e["unverified"] = False
        else:
            e["unverified"] = True
        save_audit(root, audit)

        _print_envelope(
            {"ok": True, "exitCode": 0,
             "summary": f"updated {args.snippet_id}"
                        + (" (unverified)" if args.no_validate else "")},
            args.as_json,
        )
        return 0

    snip = parse_snippet_file(existing)
    new_summary = snip["summary"]
    arg_desc_updates = {}
    for kv in args.set_field:
        if "=" not in kv:
            _print_envelope(
                {"ok": False, "exitCode": 1,
                 "summary": f"--set expects key=value, got {kv!r}"},
                args.as_json,
            )
            return 1
        k, _, v = kv.partition("=")
        k = k.strip()
        v = v.strip()
        if k == "summary":
            new_summary = v
        elif k.startswith("arg.") and k.endswith(".description"):
            argname = k[4:-len(".description")]
            if not any(a["name"] == argname for a in snip["args"]):
                _print_envelope(
                    {"ok": False, "exitCode": 1,
                     "summary": f"no such arg: {argname!r}"},
                    args.as_json,
                )
                return 1
            arg_desc_updates[argname] = v
        else:
            _print_envelope(
                {"ok": False, "exitCode": 1,
                 "summary": f"--set field {k!r} not allowed; only `summary` and "
                            f"`arg.<name>.description` can be updated without --file"},
                args.as_json,
            )
            return 1

    new_text = existing
    if new_summary != snip["summary"]:
        new_text = re.sub(
            r"(^summary:\s*).+$", rf"\g<1>{new_summary}",
            new_text, count=1, flags=re.MULTILINE,
        )
    for argname, desc in arg_desc_updates.items():
        pattern = re.compile(
            rf"(- name: {re.escape(argname)}\n(?:    [^\n]+\n)*?)"
            rf"(    description:[^\n]*\n)?",
            re.MULTILINE,
        )
        def _repl(m):
            head = m.group(1)
            new_line = f"    description: {desc}\n"
            return head + new_line
        new_text = pattern.sub(_repl, new_text, count=1)

    write_snippet_file(root, args.snippet_id, new_text)
    _print_envelope(
        {"ok": True, "exitCode": 0,
         "summary": f"updated {args.snippet_id} metadata"},
        args.as_json,
    )
    return 0
```

- [ ] **Step 4: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets update scene.count_root_objects \
    --set 'summary=Count root GameObjects (live scene)' --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets show scene.count_root_objects --json | head -10

python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets update scene.count_root_objects \
    --set 'safety=mutates' --json
```

Expected: first command updates the summary; second is rejected with "not allowed".

- [ ] **Step 5: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets update (--file revalidates, --set restricted)"
```

---

### Task 13: `cs snippets deprecate`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the `deprecate` subparser**

```python
    sp_sn_dep = sn_sub.add_parser("deprecate", parents=[shared],
                                   help="Deprecate a snippet")
    sp_sn_dep.add_argument("snippet_id")
    sp_sn_dep.add_argument("--reason", default=None)
    sp_sn_dep.add_argument("--supersede", default=None,
                           help="Id of a snippet that replaces this one")
```

- [ ] **Step 2: Add to dispatch**

```python
        elif args.snippets_cmd == "deprecate":
            sys.exit(cmd_snippets_deprecate(root, args))
```

- [ ] **Step 3: Implement**

```python
def cmd_snippets_deprecate(root, args):
    from cli.snippets.store import read_snippet_file
    from cli.snippets.stats import mark_deprecated, load_audit

    if read_snippet_file(root, args.snippet_id) is None:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"snippet not found: {args.snippet_id}"},
            args.as_json,
        )
        return 1
    audit = load_audit(root)
    if args.snippet_id not in audit["snippets"]:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"no audit entry for {args.snippet_id}"},
            args.as_json,
        )
        return 1
    if args.supersede and read_snippet_file(root, args.supersede) is None:
        _print_envelope(
            {"ok": False, "exitCode": 1,
             "summary": f"--supersede target not found: {args.supersede}"},
            args.as_json,
        )
        return 1
    mark_deprecated(root, args.snippet_id,
                    reason=args.reason, supersede=args.supersede)
    _print_envelope(
        {"ok": True, "exitCode": 0,
         "summary": f"deprecated {args.snippet_id}"
                    + (f" (superseded by {args.supersede})" if args.supersede else "")},
        args.as_json,
    )
    return 0
```

- [ ] **Step 4: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets deprecate scene.create_marker \
    --reason "test deprecation" --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets list --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets list --include-deprecated --json
```

- [ ] **Step 5: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets deprecate (with --supersede)"
```

---

### Task 14: Aging policy classification (`stats.py`)

**Files:**
- Modify: `cli/snippets/stats.py`
- Modify: `tests/test_snippets_stats.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_snippets_stats.py`:
```python
from cli.snippets.stats import classify_state, AgingPolicy


class ClassifyStateTests(unittest.TestCase):
    def setUp(self):
        self.policy = AgingPolicy(
            cold_days=90, cold_min_uses=3,
            broken_strikes=5, broken_min_span_days=7,
            hot_min_uses=10, hot_max_recency_days=7,
        )

    def _entry(self, **overrides):
        e = {
            "successes": 0, "failures": 0,
            "last_used": "2026-05-07T00:00:00Z",
            "last_failure": None,
            "first_failure_in_streak": None,
            "consecutive_failures": 0,
        }
        e.update(overrides)
        return e

    def test_hot(self):
        e = self._entry(successes=15, last_used="2026-05-06T00:00:00Z")
        self.assertEqual(
            classify_state(e, "2026-05-07T00:00:00Z", self.policy),
            "hot",
        )

    def test_cold(self):
        e = self._entry(successes=1, last_used="2026-01-01T00:00:00Z")
        self.assertEqual(
            classify_state(e, "2026-05-07T00:00:00Z", self.policy),
            "cold",
        )

    def test_broken(self):
        e = self._entry(
            consecutive_failures=5,
            first_failure_in_streak="2026-04-15T00:00:00Z",
            last_failure="2026-04-25T00:00:00Z",
        )
        self.assertEqual(
            classify_state(e, "2026-05-07T00:00:00Z", self.policy),
            "broken",
        )

    def test_broken_requires_both_strikes_and_span(self):
        e = self._entry(
            consecutive_failures=5,
            first_failure_in_streak="2026-05-01T00:00:00Z",
            last_failure="2026-05-03T00:00:00Z",
        )
        self.assertNotEqual(
            classify_state(e, "2026-05-07T00:00:00Z", self.policy),
            "broken",
        )

    def test_neutral(self):
        e = self._entry(successes=2, last_used="2026-05-07T00:00:00Z")
        self.assertEqual(
            classify_state(e, "2026-05-07T00:00:00Z", self.policy),
            "neutral",
        )
```

- [ ] **Step 2: Run tests, verify they fail**

```
python -m unittest tests.test_snippets_stats -v
```

Expected: ImportError on `classify_state` and `AgingPolicy`.

- [ ] **Step 3: Implement classification**

Append to `cli/snippets/stats.py`:
```python
from collections import namedtuple

AgingPolicy = namedtuple("AgingPolicy", [
    "cold_days", "cold_min_uses",
    "broken_strikes", "broken_min_span_days",
    "hot_min_uses", "hot_max_recency_days",
])

DEFAULT_POLICY = AgingPolicy(
    cold_days=90, cold_min_uses=3,
    broken_strikes=5, broken_min_span_days=7,
    hot_min_uses=10, hot_max_recency_days=7,
)


def _parse_iso(s):
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _days_between(a, b):
    da, db = _parse_iso(a), _parse_iso(b)
    if da is None or db is None:
        return 0
    return abs((db - da).days)


def classify_state(entry, now_iso, policy=DEFAULT_POLICY):
    """Classify a stats entry as 'hot' / 'cold' / 'broken' / 'neutral'."""
    cs = entry.get("consecutive_failures", 0)
    if cs >= policy.broken_strikes:
        span = _days_between(
            entry.get("first_failure_in_streak"),
            entry.get("last_failure"),
        )
        if span >= policy.broken_min_span_days:
            return "broken"

    last_used = entry.get("last_used")
    successes = entry.get("successes", 0)
    if last_used:
        recency = _days_between(last_used, now_iso)
        if successes >= policy.hot_min_uses and recency <= policy.hot_max_recency_days:
            return "hot"
        if recency >= policy.cold_days and successes < policy.cold_min_uses:
            return "cold"
    return "neutral"
```

- [ ] **Step 4: Run tests, verify they pass**

```
python -m unittest tests.test_snippets_stats -v
```

Expected: 12 tests, all pass.

- [ ] **Step 5: Commit**

```
git add cli/snippets/stats.py tests/test_snippets_stats.py
git commit -m "feat(snippets): aging policy classification (hot/cold/broken/neutral)"
```

---

### Task 15: `cs snippets prune`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the `prune` subparser**

```python
    sp_sn_prune = sn_sub.add_parser("prune", parents=[shared],
                                     help="Clean up the snippet library")
    sp_sn_prune.add_argument("--cold", action="store_true",
                             help="Also mark cold snippets as deprecated (opt-in)")
    sp_sn_prune.add_argument("--remove", action="store_true",
                             help="Hard-delete deprecated snippets older than --max-age-days")
    sp_sn_prune.add_argument("--max-age-days", type=int, default=30, dest="max_age_days")
    sp_sn_prune.add_argument("--dry-run", dest="dry_run", action="store_true")
```

- [ ] **Step 2: Add to dispatch**

```python
        elif args.snippets_cmd == "prune":
            sys.exit(cmd_snippets_prune(root, args))
```

- [ ] **Step 3: Implement**

```python
def cmd_snippets_prune(root, args):
    from cli.snippets.store import (snippet_path, list_snippet_ids)
    from cli.snippets.stats import (load_audit, save_audit, load_stats,
                                    save_stats, classify_state, mark_deprecated, _now)
    from datetime import datetime, timezone

    audit = load_audit(root)
    stats = load_stats(root)

    actions = {"deprecate": [], "remove": []}
    now_iso = _now()

    for sid in list_snippet_ids(root):
        a = audit["snippets"].get(sid, {})
        if a.get("deprecated"):
            continue
        entry = stats["snippets"].get(sid, {})
        state = classify_state(entry, now_iso)
        if state == "broken":
            actions["deprecate"].append((sid, state))
        elif state == "cold" and args.cold:
            actions["deprecate"].append((sid, state))

    if args.remove:
        now = datetime.now(timezone.utc)
        for sid, a in audit["snippets"].items():
            if not a.get("deprecated"):
                continue
            dep_at = a.get("deprecated_at")
            if not dep_at:
                continue
            d = datetime.strptime(dep_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if (now - d).days >= args.max_age_days:
                actions["remove"].append(sid)

    if args.dry_run:
        result = {
            "ok": True, "exitCode": 0,
            "summary": (f"plan: deprecate {len(actions['deprecate'])}, "
                        f"remove {len(actions['remove'])}"),
            "data": {
                "deprecate": [sid for sid, _ in actions["deprecate"]],
                "remove": actions["remove"],
            },
        }
        if args.as_json:
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
            print()
        else:
            print(result["summary"])
            for sid, st in actions["deprecate"]:
                print(f"  deprecate ({st}): {sid}")
            for sid in actions["remove"]:
                print(f"  remove:    {sid}")
        return 0

    for sid, state in actions["deprecate"]:
        entry = stats["snippets"].get(sid, {})
        if state == "broken":
            reason = (f"{entry.get('consecutive_failures')} consecutive failures "
                      f"between {entry.get('first_failure_in_streak')} "
                      f"and {entry.get('last_failure')}")
        else:
            reason = "cold (low usage)"
        mark_deprecated(root, sid, reason=reason)

    for sid in actions["remove"]:
        p = snippet_path(root, sid)
        try:
            p.unlink()
        except OSError:
            pass
        audit["snippets"].pop(sid, None)
        stats["snippets"].pop(sid, None)
    if actions["remove"]:
        save_audit(root, audit)
        save_stats(root, stats)

    summary = (f"deprecated {len(actions['deprecate'])}, "
               f"removed {len(actions['remove'])}")
    _print_envelope(
        {"ok": True, "exitCode": 0, "summary": summary,
         "data": {
             "deprecate": [sid for sid, _ in actions["deprecate"]],
             "remove": actions["remove"],
         }},
        args.as_json,
    )
    return 0
```

- [ ] **Step 4: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets prune --cold --dry-run --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets prune --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets prune --remove --json
```

- [ ] **Step 5: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets prune (cold opt-in, broken auto, --remove gated)"
```

---

### Task 16: `cs snippets stats`

**Files:**
- Modify: `cli/cs.py`

- [ ] **Step 1: Add the `stats` subparser**

```python
    sp_sn_stats = sn_sub.add_parser("stats", parents=[shared],
                                     help="Show usage stats")
    sp_sn_stats.add_argument("--id", dest="snippet_id", default=None,
                             help="Show stats for a single snippet (default: all)")
```

- [ ] **Step 2: Add to dispatch**

```python
        elif args.snippets_cmd == "stats":
            sys.exit(cmd_snippets_stats(root, args))
```

- [ ] **Step 3: Implement**

```python
def cmd_snippets_stats(root, args):
    from cli.snippets.stats import load_stats, classify_state, _now

    stats = load_stats(root)
    items = stats.get("snippets", {})
    rows = []
    now_iso = _now()
    target = (items.items() if not args.snippet_id
              else [(args.snippet_id, items.get(args.snippet_id))])
    for sid, entry in target:
        if entry is None:
            continue
        rows.append({
            "id": sid,
            "successes": entry.get("successes", 0),
            "failures": entry.get("failures", 0),
            "invocations": entry.get("successes", 0) + entry.get("failures", 0),
            "last_used": entry.get("last_used"),
            "consecutive_failures": entry.get("consecutive_failures", 0),
            "state": classify_state(entry, now_iso),
        })

    rows.sort(key=lambda r: -r["successes"])
    result = {
        "ok": True, "exitCode": 0,
        "summary": f"stats for {len(rows)} snippet(s)",
        "data": {"stats": rows},
    }
    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(result["summary"])
        for r in rows:
            print(f"  {r['id']:40s} successes={r['successes']:4d} "
                  f"failures={r['failures']:4d} state={r['state']}")
    return 0
```

- [ ] **Step 4: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets stats --json
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets stats --id scene.count_root_objects --json
```

- [ ] **Step 5: Commit**

```
git add cli/cs.py
git commit -m "feat(snippets): cs snippets stats (per-snippet and aggregate)"
```

---

### Task 17: Mutates safety class refusal hardening

**Files:**
- Modify: `tests/test_snippets_validate.py`

- [ ] **Step 1: Add a regression test**

Append to `tests/test_snippets_validate.py`:
```python
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
```

- [ ] **Step 2: Run validate tests**

```
python -m unittest tests.test_snippets_validate -v
```

Expected: 8 tests, all pass.

- [ ] **Step 3: Verify CLI path manually**

In a project with a mutates snippet at `/tmp/box_snip.md`:

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" snippets add scene.create_box --file /tmp/box_snip.md --json
```

Expected: `ok=false`, summary mentions safety=mutates and `--no-validate`.

- [ ] **Step 4: Commit**

```
git add tests/test_snippets_validate.py
git commit -m "test(snippets): regression test for mutates routing in validation"
```

D1 is now shippable.

---

## Phase D2 — Skill + Cross-References + Docs

### Task 18: Write `skills/unity-cli-snippets/SKILL.md`

**Files:**
- Create: `skills/unity-cli-snippets/SKILL.md`

- [ ] **Step 1: Write the skill content**

```markdown
---
name: unity-cli-snippets
description: >
  Self-evolving library of reusable C# snippets executed via cs exec. Use when
  performing Unity Editor operations that need custom code: scene queries, batch
  ops, workflow automation. Library lives in project at .unity-cli/snippets~/
  and grows through agent-distilled patterns. Triggers on any non-trivial cs
  exec scenario, recurring Unity automation, or when the user mentions "save as
  snippet" / "reuse this".
---

# Unity CLI Snippets

## Decision Order (strict)

Before writing ad-hoc `cs exec` for any non-trivial Unity automation:

1. `cs list-commands [--type custom]` — built-in or custom command available?
2. `cs snippets search <description>` — matching snippet?
3. Only if neither match: ad-hoc `cs exec`.

"Non-trivial" = >3 lines, or uses LINQ / reflection / AssetDatabase / multi-step.

**Never** `Read` or `ls` `.unity-cli/snippets~/` directly. Always go through the CLI.

## Workflow

```
search → (show) → use → (distill if reusable)
```

## CLI Quick Reference

The 5 you'll actually use:

| Command | Purpose |
|---------|---------|
| `cs snippets search <q>` | Top-N lexical hits over id + summary |
| `cs snippets show <id>` | Full body and metadata for one snippet |
| `cs snippets use <id> --args '<json>'` | Run with typed args; tracks stats |
| `cs snippets add <id> --file <md>` | Validate and register a new snippet |
| `cs snippets deprecate <id> [--supersede <new>]` | Retire a snippet without deletion |

Full set: `list / show / search / use / add / update / deprecate / prune / stats` — see `cs snippets --help`.

## Snippet Anatomy

```markdown
---
id: scene.find_active_in_layer
summary: Find active GameObjects in a specific layer
safety: read-only
args:
  - name: layerName
    type: string
example:
  layerName: "Default"
expected: ["Main Camera", "Directional Light"]   # optional
---

```csharp
using System.Linq;

static List<string> Run(string layerName) {
    return UnityEngine.Object.FindObjectsOfType<GameObject>()
        .Where(g => g.activeInHierarchy && LayerMask.LayerToName(g.layer) == layerName)
        .Select(g => g.name).ToList();
}
```
```

- Body must define one `static Run(...)` method matching `args` order.
- Helpers go alongside `Run` as `static` members. No local functions.
- The CLI wraps body+call in a unique class name on submission; symbols don't leak across snippets.

## When to Distill

All must hold:

- Code is parameterized (or trivially can be parameterized into 1–4 typed args).
- Solves a recurring concept: query, batch op, common workflow.
- User signaled "save this", OR you judge the pattern likely to recur.

## When NOT to Distill

Any one disqualifies:

- One-shot tied to an exact path/name/id.
- Trivial enough that the snippet wrapper isn't shorter than the original.
- Depends on ephemeral or generated symbols (autogen code, runtime-injected types) that won't exist after a fresh checkout.
- Half-working / WIP.

## Safety Classes

- **`read-only`** — pure query, auto-validated by `add` / `update --file`.
- **`mutates`** — side effects on scene, assets, files, settings. Cannot be auto-validated. Requires `--no-validate`; audit marks `unverified: true` and `list` prefixes the row with ⚠.

Snippets that touch `AssetDatabase`, write files, change `ProjectSettings`, trigger refreshes, or affect domain reload are always `mutates`.

## Validation Gate

`add` (and `update --file`) runs the snippet's `example` once through the REPL:

- `read-only`: must return `ok=true`. With optional `expected:` field, return value is also checked for deep equality.
- `mutates`: refused unless `--no-validate`.

The gate is a **smoke test**, not a correctness oracle. Use `expected:` for return-value assertions.

## Argument Types

| Type | JSON shape | Generated literal |
|------|-----------|-------------------|
| `string` | `"foo"` | `"foo"` (escaped) |
| `int` / `float` / `bool` | `42` / `3.14` / `true` | `42` / `3.14f` / `true` |
| `vector2` / `vector3` / `vector4` | `[x, y, ...]` | `new UnityEngine.Vector3(x, y, z)` |
| `color` | `[r, g, b]` or `[r, g, b, a]` | `new UnityEngine.Color(r, g, b, a)` |
| `string[]` / `int[]` / `float[]` | `[...]` | `new T[] { ... }` |

No `Quaternion` (use `vector3` Euler or `vector4` raw inside `Run`). No `expr` (build the expression inside `Run`). Optional args declare a `default:` field.

## Aging

`stats` fields track `successes`, `failures`, `last_used`, `consecutive_failures`. Snippets are auto-deprecated only when `consecutive_failures >= 5` AND the streak spans ≥ 7 days. Cold detection (low usage / old) is **informational** in `list --sort cold`; `prune --cold` is opt-in.

## DO NOT

- Read `.unity-cli/snippets~/` directly with shell tools.
- Hand-edit snippet `.md` files; use `add` / `update --file` so validation runs.
- Skip `cs list-commands` and `cs snippets search` before ad-hoc `cs exec`.
- Distill one-shot operations or trivial one-liners.

## Boundary with `cs command` / `cs exec`

- Built-in/custom command available → `cs command` (see `unity-cli-command` skill).
- One-off ad-hoc → `cs exec` (see `unity-cli-exec-code` skill).
- Reusable ad-hoc → `cs snippets`.
```

- [ ] **Step 2: Verify markdown renders cleanly**

Open the file in your editor; eyeball it. Word count:
```
wc -w skills/unity-cli-snippets/SKILL.md
```

Target: ≤ 800 words.

- [ ] **Step 3: Commit**

```
git add skills/unity-cli-snippets/SKILL.md
git commit -m "feat(skill): unity-cli-snippets skill (operator's manual)"
```

---

### Task 19: Cross-references in existing skills

**Files:**
- Modify: `skills/unity-cli-command/SKILL.md`
- Modify: `skills/unity-cli-exec-code/SKILL.md`

- [ ] **Step 1: Add cross-reference to `unity-cli-command/SKILL.md`**

Find the "Command-First Principle" section. After its existing paragraph, add:

```markdown
If no built-in or custom command matches the task, **next** check `unity-cli-snippets` (run `cs snippets search <description>`) before falling back to ad-hoc `cs exec` via `unity-cli-exec-code`. The decision order is: command → snippet → ad-hoc.
```

- [ ] **Step 2: Add cross-reference to `unity-cli-exec-code/SKILL.md`**

Find the introductory section. After "Always prefer the `unity-cli-command` skill first.", add:

```markdown
Then check the snippet library (`cs snippets search <description>`) before writing ad-hoc code. After solving a non-trivial task that's likely to recur, consider distilling it into a snippet — see the `unity-cli-snippets` skill.
```

- [ ] **Step 3: Commit**

```
git add skills/unity-cli-command/SKILL.md skills/unity-cli-exec-code/SKILL.md
git commit -m "docs(skills): cross-reference unity-cli-snippets in command and exec skills"
```

---

### Task 20: `.gitignore` integration in `cs setup`

**Files:**
- Modify: `cli/cs.py` (extend `cmd_setup`)

- [ ] **Step 1: Add the helper**

In `cli/cs.py`, alongside other helpers (before `cmd_setup`):

```python
_GITIGNORE_BLOCK_LINES = [
    "# unity-cli-plugin: snippet stats are observability data, not project state",
    ".unity-cli/snippets-stats.json",
]


def _ensure_gitignore_entry(project_root):
    """Append snippet-stats lines to project .gitignore if not already present.

    Idempotent: scans for the exact path line before appending.
    """
    gitignore = Path(project_root) / ".gitignore"
    existing = ""
    if gitignore.is_file():
        try:
            existing = gitignore.read_text(encoding="utf-8")
        except OSError:
            return  # silently skip — not fatal
    target = ".unity-cli/snippets-stats.json"
    for line in existing.splitlines():
        if line.strip() == target:
            return
    block = ("\n" if existing and not existing.endswith("\n") else "") \
            + "\n".join(_GITIGNORE_BLOCK_LINES) + "\n"
    try:
        with gitignore.open("a", encoding="utf-8") as f:
            f.write(block)
    except OSError:
        pass
```

- [ ] **Step 2: Wire into `cmd_setup`**

In `cmd_setup`, just before `return 0` at the end of the success path (where the manifest has been written), add:

```python
    _ensure_gitignore_entry(root)
```

- [ ] **Step 3: Smoke-test**

```
python "${CLAUDE_PLUGIN_ROOT}/cli/cs.py" setup
cat <project>/.gitignore
```

Expected: the two lines from `_GITIGNORE_BLOCK_LINES` appear at the end. Run setup again — they don't duplicate.

- [ ] **Step 4: Commit**

```
git add cli/cs.py
git commit -m "feat(setup): auto-add snippet stats to project .gitignore"
```

---

### Task 21: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add `cs snippets` to the commands table**

Find the `### Commands` table in `CLAUDE.md`. Append rows after `cs catalog list`:

```markdown
| `cs snippets list \| show \| search \| use` | post | Browse and run reusable C# snippets |
| `cs snippets add \| update \| deprecate \| prune \| stats` | post | Manage snippet library |
```

- [ ] **Step 2: Add a "Snippet Library" subsection**

After the `## Command Catalog` section, add:

```markdown
## Snippet Library

Self-evolving project-local library of reusable C# snippets executed via `cs exec` (no Unity compilation involvement). Snippet bodies live at `<project>/.unity-cli/snippets~/<id>.md`; audit is committed, stats are gitignored. The plugin ships a `unity-cli-snippets` skill as the agent's operator manual; the skill instructs the agent to follow the decision order: built-in/custom command → snippet → ad-hoc `cs exec`.

See `skills/unity-cli-snippets/SKILL.md` for usage rules and `cs snippets --help` for the full CLI.
```

- [ ] **Step 3: Commit**

```
git add CLAUDE.md
git commit -m "docs: add snippet library to CLAUDE.md"
```

---

### Task 22: Update READMEs (EN + CN)

**Files:**
- Modify: `README.md`
- Modify: `README_zh.md`

- [ ] **Step 1: English README**

Find the features section. Add a bullet:

```markdown
- **Self-evolving snippet library** — project-local C# snippets (`.md` files, no compilation) with validation gate, usage tracking, and aging. Discover and grow via `cs snippets` and the `unity-cli-snippets` skill.
```

In the commands table, add rows mirroring CLAUDE.md.

- [ ] **Step 2: Chinese README**

Mirror the same change in `README_zh.md`. Suggested copy:

```markdown
- **自我进化的代码片段库** — 项目本地 C# 片段（`.md` 文件，不参与编译），带验证门、使用频次跟踪、自动老化。通过 `cs snippets` 子命令和 `unity-cli-snippets` skill 发现和演化。
```

- [ ] **Step 3: Commit**

```
git add README.md README_zh.md
git commit -m "docs: add snippet library to READMEs (EN + CN)"
```

---

### Task 23: CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add to `## [Unreleased]`**

Under the `## [Unreleased]` heading, add:

```markdown
### Added

- Self-evolving C# snippet library: `cs snippets list / show / search / use /
  add / update / deprecate / prune / stats`. Snippets are project-local markdown
  files at `.unity-cli/snippets~/<id>.md` containing a `static Run(...)` method;
  the CLI wraps each submission in a unique `static class __Snip_<hash>` for
  symbol isolation across REPL sessions. Validation gate runs each new snippet's
  `example` through the REPL (read-only auto-validated; mutates requires
  `--no-validate` and is recorded as unverified). Usage tracking auto-deprecates
  snippets after 5 consecutive failures spanning ≥ 7 days. Cold detection is
  informational only; `prune --cold` is opt-in.
- `unity-cli-snippets` skill: operator's manual for the snippet library, with
  hard decision order (command → snippet → ad-hoc) and distill criteria.
- `cs setup` automatically adds `.unity-cli/snippets-stats.json` to the project
  `.gitignore` to avoid PR churn from routine usage tracking. The audit file
  (`snippets-audit.json`) remains committed as project state.
```

- [ ] **Step 2: Commit**

```
git add CHANGELOG.md
git commit -m "docs: changelog entry for snippet library"
```

D2 ready to ship. After merging, the next version bump (per `CLAUDE.md` release process) renames `## [Unreleased]` → `## [X.Y.Z]` and tags.

---

## Verification Checklist (run before declaring the plan complete)

- [ ] All unit tests pass: `python -m unittest discover tests -v`
- [ ] D0 smoke-test results captured at `docs/superpowers/notes/2026-05-07-d0-smoke-results.md`
- [ ] On a fresh Unity project: `cs setup` adds `.gitignore` line; `cs snippets add` + `use` round-trip works for a `read-only` snippet; `mutates` snippet is refused without `--no-validate`.
- [ ] `cs snippets search` returns hits for partial-match queries.
- [ ] `cs snippets deprecate` hides from default `list`; `--include-deprecated` shows it.
- [ ] `cs snippets prune --cold --dry-run` reports cold candidates without acting.
- [ ] `cs snippets stats` shows accurate `successes` / `failures` / `state` per snippet.
- [ ] `unity-cli-snippets` skill markdown renders correctly and stays under 800 words.
- [ ] CLAUDE.md, README.md, README_zh.md, CHANGELOG.md all updated.
- [ ] `git log --oneline` shows one commit per task (no batch commits).
