import json
import os
import subprocess
import sys
import tempfile
import unittest

from amlang.check import check_source


class CheckSourceTests(unittest.TestCase):
    def test_clean_code(self):
        self.assertEqual(check_source("print('hi')\n"), [])

    def test_does_not_run_the_code(self):
        self.assertEqual(check_source("raise SystemExit('ran!')\n1 / 0\n"), [])

    def test_python_syntax_error(self):
        [p] = check_source("if True\n    print(1)\n")
        self.assertEqual((p["line"], p["severity"]), (1, "error"))
        self.assertIn("missing ':'", p["hint"])

    def test_am_error_and_earlier_warning_both_reported(self):
        src = "x = 0.1 + 0.2\nprint(x == 0.3)\ncount = 0\ndef inc():\n    count += 1\n"
        problems = check_source(src)
        self.assertEqual([(p["line"], p["severity"]) for p in problems], [(2, "warning"), (5, "error")])
        self.assertEqual(problems[1]["column"], 5)
        self.assertIn("global count", problems[1]["hint"])


class CheckCliTests(unittest.TestCase):
    def am(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-m", "amlang", *args], input=stdin, capture_output=True, text=True)

    def test_json_from_stdin(self):
        result = self.am("--check", "--json", "-", stdin="list = [1]\n")
        self.assertEqual(result.returncode, 1)
        [p] = json.loads(result.stdout)
        self.assertEqual((p["line"], p["column"]), (1, 1))
        self.assertIn("my_list", p["hint"])

    def test_text_output_for_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ok.am")
            with open(path, "w") as f:
                f.write("print(1)\n")
            result = self.am("--check", path)
        self.assertEqual(result.returncode, 0)
        self.assertIn("No problems found.", result.stdout)

    def test_warnings_only_exit_zero(self):
        result = self.am("--check", "--json", "-", stdin="print(0.5 == 0.5)\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["severity"], "warning")


if __name__ == "__main__":
    unittest.main()
