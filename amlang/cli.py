import code
import os
import sys

from . import compile_am, new_globals, run_file


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


def main():
    args = sys.argv[1:]
    if not args:
        AmConsole(new_globals(filename="<am>")).interact(banner="AM language (type exit() to quit)", exitmsg="")
        return
    path = args[0]
    sys.argv = args
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    try:
        run_file(path)
    except SyntaxError as e:
        sys.exit(f"AM error: {e.msg}" if e.msg.startswith("line") else f"AM error: line {e.lineno}: {e.msg}")


if __name__ == "__main__":
    main()
