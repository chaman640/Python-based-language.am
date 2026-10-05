import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

from amlang import compile_am, new_globals

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def run(source):
    out = io.StringIO()
    with redirect_stdout(out):
        exec(compile_am(source), new_globals())
    return out.getvalue()


class FixTests(unittest.TestCase):
    def test_mutable_default_list_is_fresh(self):
        src = "def f(x, items=[]):\n    items.append(x)\n    return items\nprint(f(1), f(2))\n"
        self.assertEqual(run(src), "[1] [2]\n")

    def test_mutable_default_dict_and_kwonly(self):
        src = "def f(k, *, d={}):\n    d[k] = 1\n    return d\nprint(f('a'), f('b'))\n"
        self.assertEqual(run(src), "{'a': 1} {'b': 1}\n")

    def test_explicit_argument_still_used(self):
        src = "def f(items=[]):\n    items.append(1)\n    return items\nmine = [0]\nf(mine)\nprint(mine)\n"
        self.assertEqual(run(src), "[0, 1]\n")

    def test_is_with_literal_compares_values(self):
        self.assertEqual(run("a = 1000\nb = 999 + 1\nprint(a is 1000, b is not 1000)\n"), "True False\n")

    def test_is_none_unchanged(self):
        self.assertEqual(run("x = None\nprint(x is None)\n"), "True\n")

    def test_bare_except_does_not_catch_keyboard_interrupt(self):
        src = "try:\n    raise KeyboardInterrupt\nexcept:\n    print('caught')\n"
        with self.assertRaises(KeyboardInterrupt):
            run(src)

    def test_bare_except_still_catches_errors(self):
        self.assertEqual(run("try:\n    1 / 0\nexcept:\n    print('caught')\n"), "caught\n")

    def test_overwriting_builtin_is_an_error(self):
        with self.assertRaises(SyntaxError) as ctx:
            compile_am("list = [1, 2]\n")
        self.assertIn("'list' is a built-in name", str(ctx.exception))


class ToolingTests(unittest.TestCase):
    def test_cli_runs_example_with_am_import(self):
        result = subprocess.run(
            [sys.executable, "-m", "amlang", os.path.join(EXAMPLES, "main.am")],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.splitlines()[1:3], ["[1]", "[2]"])

    def test_python_can_import_am_module(self):
        sys.path.insert(0, EXAMPLES)
        try:
            from helpers import add_item
        finally:
            sys.path.remove(EXAMPLES)
        self.assertEqual((add_item(1), add_item(2)), ([1], [2]))


if __name__ == "__main__":
    unittest.main()
