import code
import os
import sys
import traceback

from . import compile_am, new_globals, run_file
from .errors import format_error

USAGE = """usage: am [--traceback] [file.am] [args...]

  am                 start the interactive prompt
  am file.am         run a file
  --traceback        show the full Python traceback on errors
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
    show_traceback = "--traceback" in args[:1]
    if show_traceback:
        args = args[1:]
    if args[:1] in (["-h"], ["--help"]):
        print(USAGE, end="")
        return
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


def _report(exc, show_traceback):
    if show_traceback:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
    else:
        print(format_error(exc), file=sys.stderr)
        print("\n(run with 'am --traceback ...' to see the full Python traceback)", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
