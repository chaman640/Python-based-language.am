import code
import json
import os
import sys
import traceback

from . import __version__, compile_am, new_globals, run_file
from .errors import format_error

USAGE = """usage: am [--traceback] [file.am] [args...]
       am --check [--json] file.am

  am                       start the interactive prompt
  am file.am               run a file
  am --traceback file.am   run, showing the full Python traceback on errors
  am --check file.am       find errors and warnings without running the file
                           (use - as the file name to read code from stdin)
  --json                   with --check: print the problems as JSON (for editors)
  --version                show the AM version
"""


class AmConsole(code.InteractiveConsole):
    def runsource(self, source, filename="<am>", symbol="single"):
        try:
            compiled = self.compile(source, filename, symbol)  # incomplete input check
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False
        if compiled is None:
            return True
        try:
            self.runcode(compile_am(source, filename, symbol))
        except SyntaxError:
            self.showsyntaxerror(filename)
        return False

    def showtraceback(self):
        self.write(format_error(sys.exc_info()[1]) + "\n")

    def showsyntaxerror(self, filename=None, **kwargs):
        self.write(format_error(sys.exc_info()[1]) + "\n")


def main():
    args = sys.argv[1:]
    flags = set()
    while args and args[0] in ("--traceback", "--check", "--json", "--version", "-h", "--help"):
        flags.add(args.pop(0))
    if "--version" in flags:
        print(f"AM {__version__}")
        return
    if flags & {"-h", "--help"}:
        print(USAGE, end="")
        return
    if "--check" in flags:
        if len(args) != 1:
            sys.exit("usage: am --check [--json] file.am")
        sys.exit(check(args[0], as_json="--json" in flags))
    show_traceback = "--traceback" in flags
    if not args:
        AmConsole(new_globals(filename="<am>")).interact(banner="AM language (type exit() to quit)", exitmsg="")
        return

    path = args[0]
    sys.argv = args
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    try:
        run_file(path)
    except KeyboardInterrupt:
        sys.exit(130)
    except FileNotFoundError as e:
        if e.filename == path:
            sys.exit(f"am: file not found: {path}")
        _report(e, show_traceback)
    except Exception as e:
        _report(e, show_traceback)


def check(path, as_json=False):
    """Print the problems in a file. Returns the exit code: 1 if there are errors."""
    from .check import check_source, format_problems

    try:
        if path == "-":
            source = sys.stdin.read()
        else:
            with open(path, encoding="utf-8") as f:
                source = f.read()
    except OSError:
        print(f"am: file not found: {path}", file=sys.stderr)
        return 2
    problems = check_source(source, "<stdin>" if path == "-" else path)
    print(json.dumps(problems) if as_json else format_problems(problems, path))
    return 1 if any(p["severity"] == "error" for p in problems) else 0


def _report(exc, show_traceback):
    if show_traceback:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
    else:
        print(format_error(exc), file=sys.stderr)
        print("\n(run with 'am --traceback ...' to see the full Python traceback)", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
