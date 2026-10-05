"""AM: Python syntax, Python libraries, fewer Python bugs."""
import ast
import importlib.machinery
import importlib.util
import linecache
import os
import sys
import warnings

from .fixer import MISSING, Fixer

__version__ = "0.1.1"
__all__ = ["AmWarning", "compile_am", "run_file"]


class AmWarning(UserWarning):
    """A likely bug found while compiling AM code. The program still runs."""


def compile_am(source, filename="<am>", mode="exec"):
    """Parse AM source, apply the bug fixes, and return a Python code object."""
    if not os.path.exists(filename):
        # Let error messages show the code line even when it isn't in a file.
        linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)
    fixer = Fixer()
    try:
        tree = fixer.visit(ast.parse(source, filename, mode))
    except SyntaxError as e:
        # Errors raised by the Fixer don't know the file yet; fill it in.
        if e.filename is None:
            e.filename = filename
            lines = source.splitlines()
            if e.lineno and e.lineno <= len(lines):
                e.text = lines[e.lineno - 1]
        raise
    finally:
        # Show warnings found so far, even if an error stopped the check.
        for lineno, message in fixer.warnings:
            warnings.warn_explicit(message, AmWarning, filename, lineno)
    return compile(ast.fix_missing_locations(tree), filename, mode)


def new_globals(name="__main__", filename="<am>"):
    return {"__name__": name, "__file__": filename, MISSING: object()}


def run_file(path):
    with open(path, encoding="utf-8") as f:
        code = compile_am(f.read(), path)
    exec(code, new_globals(filename=path))


def _format_warning(message, category, filename, lineno, line=None):
    if not issubclass(category, AmWarning):
        return _python_format_warning(message, category, filename, lineno, line)
    code_line = (line or linecache.getline(filename, lineno)).strip()
    short = filename.replace("\\", "/").rsplit("/", 1)[-1]
    shown = f"\n    {code_line}" if code_line else ""
    return f"Warning in {short}, line {lineno}:{shown}\nHint: {message}\n\n"


_python_format_warning = warnings.formatwarning
warnings.formatwarning = _format_warning


class AmLoader(importlib.machinery.SourceFileLoader):
    """Lets `import utils` find utils.am, from AM or from plain Python."""

    def get_code(self, fullname):
        # Always compile from source, so a newer amlang never runs stale bytecode.
        path = self.get_filename(fullname)
        return compile_am(importlib.util.decode_source(self.get_data(path)), path)

    def exec_module(self, module):
        setattr(module, MISSING, object())
        super().exec_module(module)


def install_import_hook():
    for i, hook in enumerate(sys.path_hooks):
        if getattr(hook, "__name__", "") == "path_hook_for_FileFinder":
            sys.path_hooks[i] = importlib.machinery.FileFinder.path_hook(
                (AmLoader, [".am"]),
                (importlib.machinery.ExtensionFileLoader, importlib.machinery.EXTENSION_SUFFIXES),
                (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES),
                (importlib.machinery.SourcelessFileLoader, importlib.machinery.BYTECODE_SUFFIXES),
            )
            sys.path_importer_cache.clear()
            return


install_import_hook()
