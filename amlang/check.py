"""Find AM errors and warnings without running the program (used by editors)."""
import warnings

from . import AmWarning, compile_am
from .errors import hint_for


def check_source(source, filename="<am>"):
    """Return a list of problems: dicts with line, column, severity, message, hint."""
    problems = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", AmWarning)
        try:
            compile_am(source, filename)
        except SyntaxError as e:
            problems.append({
                "line": e.lineno or 1,
                "column": e.offset or 1,
                "end_line": getattr(e, "end_lineno", None) or e.lineno or 1,
                "end_column": getattr(e, "end_offset", None) or None,
                "severity": "error",
                "message": f"{type(e).__name__}: {e.msg}",
                "hint": hint_for(e),
            })
    for w in caught:
        if issubclass(w.category, AmWarning):
            problems.append({
                "line": w.lineno,
                "column": 1,
                "end_line": w.lineno,
                "end_column": None,
                "severity": "warning",
                "message": str(w.message),
                "hint": None,
            })
    return sorted(problems, key=lambda p: (p["line"], p["column"]))


def format_problems(problems, filename):
    lines = []
    for p in problems:
        lines.append(f"{filename}:{p['line']}:{p['column']}: {p['severity']}: {p['message']}")
        if p["hint"]:
            lines.append(f"    Hint: {p['hint']}")
    lines.append("No problems found." if not problems else f"{len(problems)} problem(s) found.")
    return "\n".join(lines)
