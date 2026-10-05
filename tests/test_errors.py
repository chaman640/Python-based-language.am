import os
import subprocess
import sys
import tempfile
import unittest

from amlang import compile_am, new_globals
from amlang.errors import format_error


def error_for(source, filename="test.am"):
    try:
        exec(compile_am(source, filename), new_globals(filename=filename))
    except Exception as e:
        return format_error(e)
    raise AssertionError("no error raised")


class HintTests(unittest.TestCase):
    def test_name_typo_suggests_close_name(self):
        self.assertIn("Did you mean 'name'?", error_for("name = 'Anuj'\nprint(nmae)\n"))

    def test_text_plus_number(self):
        self.assertIn("mixing text and numbers", error_for("age = 21\nprint('Age: ' + age)\n"))

    def test_none_value(self):
        self.assertIn("This value is None", error_for("def f():\n    pass\nf().upper()\n"))

    def test_attribute_typo(self):
        self.assertIn("Did you mean '.upper'?", error_for("'hi'.uper()\n"))

    def test_missing_module(self):
        self.assertIn("pip install not_a_real_module", error_for("import not_a_real_module\n"))

    def test_zero_division(self):
        self.assertIn("divided by zero", error_for("print(1 / 0)\n"))

    def test_local_variable_read_before_set_in_function(self):
        msg = error_for("count = 0\ndef show():\n    print(count)\n    count = 5\nshow()\n")
        self.assertIn("UnboundLocalError", msg)
        self.assertIn("'count' is changed inside this function", msg)

    def test_outer_variable_changed_is_found_before_running(self):
        msg = error_for("print('ran')\ncount = 0\ndef inc():\n    count += 1\n")
        self.assertIn("Error in test.am, line 4:", msg)
        self.assertIn("Add 'global count'", msg)

    def test_key_error(self):
        msg = error_for("d = {}\nd['x']\n")
        self.assertIn("'x' is not in the dictionary", msg)
        self.assertIn(".get(key)", msg)

    def test_missing_colon(self):
        msg = error_for("if True\n    print(1)\n")
        self.assertIn("missing ':'", msg)

    def test_builtin_name(self):
        msg = error_for("list = [1]\n")
        self.assertIn("Error in test.am, line 1:", msg)
        self.assertIn("for example 'my_list'", msg)


class LocationTests(unittest.TestCase):
    def test_shows_file_line_and_code(self):
        msg = error_for("x = 1\ny = 2\nprint(z)\n")
        self.assertTrue(msg.startswith("Error in test.am, line 3:\n    print(z)\n"))

    def test_names_library_when_error_is_inside_it(self):
        msg = error_for("import json\njson.loads('{bad')\n")
        self.assertIn("line 2 (inside 'json')", msg)


class CliTests(unittest.TestCase):
    def run_am(self, source, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "prog.am")
            with open(path, "w") as f:
                f.write(source)
            return subprocess.run([sys.executable, "-m", "amlang", *flags, path], capture_output=True, text=True)

    def test_friendly_error_and_exit_code(self):
        result = self.run_am("print(1 / 0)\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error in prog.am, line 1:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_traceback_flag_shows_python_traceback(self):
        result = self.run_am("print(1 / 0)\n", "--traceback")
        self.assertIn("Traceback (most recent call last)", result.stderr)

    def test_missing_file(self):
        result = subprocess.run([sys.executable, "-m", "amlang", "nope.am"], capture_output=True, text=True)
        self.assertIn("file not found: nope.am", result.stderr)


if __name__ == "__main__":
    unittest.main()
