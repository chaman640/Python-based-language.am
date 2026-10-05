import io
import unittest
import warnings
from contextlib import redirect_stdout

from amlang import AmWarning, compile_am, new_globals


def run(source):
    out = io.StringIO()
    with redirect_stdout(out):
        exec(compile_am(source, "test.am"), new_globals())
    return out.getvalue()


class LoopVariableTests(unittest.TestCase):
    def test_lambda_in_comprehension(self):
        self.assertEqual(run("fs = [lambda: i for i in range(3)]\nprint([f() for f in fs])\n"), "[0, 1, 2]\n")

    def test_lambda_in_for_loop_keeps_arguments(self):
        src = "fs = []\nfor i in range(3):\n    fs.append(lambda x: x * i)\nprint([f(10) for f in fs])\n"
        self.assertEqual(run(src), "[0, 10, 20]\n")

    def test_def_in_for_loop(self):
        src = (
            "fs = []\n"
            "for name in ['a', 'b']:\n"
            "    def hello():\n"
            "        return 'hi ' + name\n"
            "    fs.append(hello)\n"
            "print([f() for f in fs], hello.__name__)\n"
        )
        self.assertEqual(run(src), "['hi a', 'hi b'] hello\n")

    def test_nested_loops(self):
        src = "fs = [lambda: (i, j) for i in range(2) for j in range(2)]\nprint([f() for f in fs])\n"
        self.assertEqual(run(src), "[(0, 0), (0, 1), (1, 0), (1, 1)]\n")

    def test_default_argument_idiom_still_works(self):
        self.assertEqual(run("fs = [lambda i=i: i for i in range(3)]\nprint([f() for f in fs])\n"), "[0, 1, 2]\n")

    def test_recursive_function_made_in_loop(self):
        src = "for n in [4]:\n    def fact(k):\n        return 1 if k <= 1 else k * fact(k - 1)\n    print(fact(n))\n"
        self.assertEqual(run(src), "24\n")

    def test_functions_outside_loops_unchanged(self):
        src = "x = 1\nf = lambda: x\nx = 2\nprint(f())\n"
        self.assertEqual(run(src), "2\n")

    def test_loop_variable_changed_inside_function_stays_local(self):
        src = "for i in range(2):\n    def f():\n        i = 'local'\n        return i\nprint(f())\n"
        self.assertEqual(run(src), "local\n")


class DecimalCompareTests(unittest.TestCase):
    def warnings_for(self, source):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            compile_am(source, "test.am")
        return [w for w in caught if issubclass(w.category, AmWarning)]

    def test_warns_on_decimal_equality(self):
        found = self.warnings_for("total = 0.1 + 0.2\nprint(total == 0.3)\n")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].lineno, 2)
        self.assertIn("math.isclose", str(found[0].message))

    def test_no_warning_for_whole_numbers_or_less_than(self):
        self.assertEqual(self.warnings_for("x = 1.5\nprint(x == 1.0, x < 0.3, x != 2)\n"), [])


class OuterVariableTests(unittest.TestCase):
    def test_augmented_assign_on_global_is_an_error(self):
        with self.assertRaises(SyntaxError) as ctx:
            compile_am("count = 0\ndef inc():\n    count += 1\n")
        self.assertEqual(ctx.exception.lineno, 3)
        self.assertIn("global count", ctx.exception.hint)

    def test_nested_function_suggests_nonlocal(self):
        with self.assertRaises(SyntaxError) as ctx:
            compile_am("def outer():\n    total = 0\n    def inner():\n        total += 1\n")
        self.assertIn("nonlocal total", ctx.exception.hint)

    def test_valid_code_is_allowed(self):
        src = (
            "count = 0\n"
            "def inc():\n    global count\n    count += 1\n"
            "def local():\n    n = 0\n    n += 1\n    return n\n"
            "def param(n):\n    n += 1\n    return n\n"
            "def walrus(xs):\n    [last := x for x in xs]\n    last += 1\n    return last\n"
            "inc()\nprint(count, local(), param(1), walrus([1, 2]))\n"
        )
        self.assertEqual(run(src), "1 1 2 3\n")


if __name__ == "__main__":
    unittest.main()
