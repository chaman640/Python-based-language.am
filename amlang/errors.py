"""Short, beginner-friendly error messages instead of Python tracebacks."""
import builtins
import difflib
import re
import sys
import traceback


def is_am_file(filename):
    return filename.endswith(".am") or filename == "<am>"


def format_error(exc):
    """Return a short message: where it happened, what happened, how to fix it."""
    parts = []
    location = _location(exc)
    if location:
        parts.append(location)
    parts.append(f"{type(exc).__name__}: {_message(exc)}")
    hint = _hint(exc)
    if hint:
        parts.append(f"Hint: {hint}")
    return "\n".join(parts)


# ---------------------------------------------------------------- location

def _location(exc):
    if isinstance(exc, SyntaxError):
        if not exc.lineno:
            return None
        lines = [f"Error in {_short(exc.filename)}, line {exc.lineno}:"]
        if exc.text:
            text = exc.text.rstrip("\n")
            indent = len(text) - len(text.lstrip())
            lines.append("    " + text.strip())
            if exc.offset and exc.offset > indent:
                lines.append("    " + " " * (exc.offset - 1 - indent) + "^")
        return "\n".join(lines) + "\n"

    frames = traceback.extract_tb(exc.__traceback__)
    user = [f for f in frames if is_am_file(f.filename)]
    if not user:
        return None
    frame = user[-1]
    where = f"Error in {_short(frame.filename)}, line {frame.lineno}"
    library = _library_name(frames[-1].filename) if frames[-1] is not frame else None
    if library:
        where += f" (inside '{library}')"
    lines = [where + ":"]
    if frame.line:
        lines.append("    " + frame.line.strip())
    return "\n".join(lines) + "\n"


def _short(filename):
    return filename.replace("\\", "/").rsplit("/", 1)[-1] if filename else "<am>"


def _library_name(filename):
    if is_am_file(filename):
        return None
    for name, module in list(sys.modules.items()):
        if getattr(module, "__file__", None) == filename:
            return name.split(".")[0]
    return _short(filename)


# ---------------------------------------------------------------- message

def _message(exc):
    if isinstance(exc, SyntaxError):
        return exc.msg
    if isinstance(exc, KeyError) and exc.args:
        return f"{exc.args[0]!r} is not in the dictionary"
    return str(exc) or "(no details)"


# ---------------------------------------------------------------- hints

def _hint(exc):
    msg = str(exc)

    if getattr(exc, "hint", None):
        return exc.hint

    if isinstance(exc, SyntaxError):
        if isinstance(exc, (IndentationError, TabError)):
            return "Use 4 spaces for each indent level, and do not mix tabs and spaces."
        return "Check this line (and the one above) for a missing ':', bracket or quote."

    if "NoneType" in msg:
        return ("This value is None. A function probably returned nothing: check that it has a "
                "'return', or check 'if value is None' before using it.")

    if isinstance(exc, UnboundLocalError):
        name = _quoted_name(msg)
        return (f"'{name}' is changed inside this function, so Python treats it as a new local variable. "
                f"Pass it in as an argument and return the new value instead.")

    if isinstance(exc, NameError):
        name = getattr(exc, "name", None) or _quoted_name(msg)
        frame = _last_frame(exc)
        names = set(dir(builtins))
        if frame is not None:
            names |= set(frame.f_globals) | set(frame.f_locals)
        match = _closest(name, names)
        if match:
            return f"Did you mean '{match}'?"
        return f"'{name}' is used before it is created. Check the spelling, or create it first with {name} = ..."

    if isinstance(exc, AttributeError):
        obj, name = getattr(exc, "obj", None), getattr(exc, "name", None)
        if obj is None:
            # Python 3.9 has no exc.obj / exc.name: read them from the message.
            parsed = re.match(r"'(\w+)' object has no attribute '(\w+)'", msg)
            if parsed:
                obj, name = getattr(builtins, parsed.group(1), None), parsed.group(2)
        if obj is not None and name:
            match = _closest(name, [a for a in dir(obj) if not a.startswith("_")])
            if match:
                return f"Did you mean '.{match}'?"
        return "Check the spelling. Use dir(value) to see what this value has."

    if isinstance(exc, ModuleNotFoundError):
        name = (exc.name or _quoted_name(msg) or "").split(".")[0]
        return f"Install it with: pip install {name}"

    if isinstance(exc, ZeroDivisionError):
        return "You divided by zero. Check the number before dividing, e.g. 'if b != 0:'."

    if isinstance(exc, TypeError):
        if re.search(r"concatenate str|'(int|float)' and 'str'|'str' and '(int|float)'", msg):
            return "You are mixing text and numbers. Use str(x) to turn a number into text, or int(x) / float(x) to turn text into a number."
        if re.search(r"positional argument|required .*argument|unexpected keyword", msg):
            return "The function got a different number of values than it expects. Compare the call with its 'def' line."
        if "not callable" in msg:
            return "You used () on something that is not a function. Check for a missing operator, like 2 * (x) instead of 2(x)."
        if "not subscriptable" in msg:
            return "You used [ ] on a value that is not a list, dict or string."

    if isinstance(exc, IndexError):
        return "The position is outside the list. A list with n items has positions 0 to n-1. Use len(...) to check."

    if isinstance(exc, KeyError):
        return "Use .get(key) to get None instead of an error, or check with 'if key in my_dict:'."

    if isinstance(exc, ValueError) and "invalid literal for int()" in msg:
        return "This text is not a whole number. Check the input, or use float() for decimal numbers."

    if isinstance(exc, FileNotFoundError):
        return "Check the file name, and that the file is in the folder you run 'am' from."

    if isinstance(exc, RecursionError):
        return "The function keeps calling itself. Make sure it has a condition where it stops."

    return None


def _quoted_name(msg):
    match = re.search(r"'([^']+)'", msg)
    return match.group(1) if match else ""


def _closest(name, candidates):
    candidates = [c for c in candidates if not c.startswith("__")]
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.7)
    return matches[0] if matches else None


def _last_frame(exc):
    tb = exc.__traceback__
    while tb is not None and tb.tb_next is not None:
        tb = tb.tb_next
    return tb.tb_frame if tb is not None else None
