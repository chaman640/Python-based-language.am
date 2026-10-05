# AM programming language

**AM** is a free programming language created by **Anuj Mishra**. It looks
exactly like Python, runs every Python library, and fixes common Python bugs
automatically. Files end in `.am`. If you know Python, you already know AM.

[Website](https://chaman640.github.io/Python-based-language.am/) ·
[PyPI: am-language](https://pypi.org/project/am-language/) ·
[VS Code extension](https://marketplace.visualstudio.com/items?itemName=chaman640.am-language)

## Install

```bash
pip install am-language
```

Or from source (to work on AM itself):

```bash
git clone https://github.com/chaman640/Python-based-language.am.git
cd Python-based-language.am
pip install -e .
```

Check it works: `am --version`

## Use

```bash
am hello.am      # run a file
am               # interactive prompt (like python's >>>)
am --traceback hello.am   # show the full Python traceback on errors
am --check hello.am       # find errors and warnings without running
```

```python
# hello.am
import json                 # any Python library works
from helpers import add_item  # other .am files can be imported too

print(json.dumps({"lang": "AM"}))
```

Plain Python can import `.am` files as well:

```python
import amlang          # turns on .am imports
from helpers import add_item
```

## Bugs AM fixes

Bugs 1-5 are fixed automatically. 4, 6 and 7 are reported before the program runs.

| # | Python problem | What AM does |
|---|---|---|
| 1 | `def f(items=[])` shares one list between all calls | Every call gets a fresh `[]`, `{}` or `set()` |
| 2 | `x is 1000` is sometimes True, sometimes False | `is` with a number or string compares values (`==`). `is None` is unchanged |
| 3 | Bare `except:` also catches Ctrl+C | It becomes `except Exception:` |
| 4 | `list = [1, 2]` silently breaks the built-in `list` | Clear error: `'list' is a built-in name, choose another name` |
| 5 | `[lambda: i for i in range(3)]` gives functions that all return `2` | Functions made in a loop remember the loop value of *that* round: `0, 1, 2` |
| 6 | `0.1 + 0.2 == 0.3` is `False` | Warning before the program runs, suggesting `math.isclose(a, b)` |
| 7 | `count += 1` in a function crashes with `UnboundLocalError` when `count` is outside it | Clear error before the program runs: add `global count` (or `nonlocal`) |

The fixes apply only to `.am` files. Library code is never changed, so every
library behaves exactly as it does in Python.

## Friendly errors

Instead of a long Python traceback, AM shows where the error is, what went
wrong, and how to fix it:

```
Error in main.am, line 2:
    print(nmae)

NameError: name 'nmae' is not defined
Hint: Did you mean 'name'?
```

```
Error in main.am, line 2:
    print("Age: " + age)

TypeError: can only concatenate str (not "int") to str
Hint: You are mixing text and numbers. Use str(x) to turn a number into text, or int(x) / float(x) to turn text into a number.
```

Run `am --traceback file.am` to see the full Python traceback.

## VS Code

Install **AM Language** from the
[VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=chaman640.am-language)
(search "AM Language" in the Extensions panel). It gives `.am` files Python
colours, auto-indent, errors and hints while you type, and a ▶ Run button.
The code is in [`editors/vscode`](editors/vscode).

## How it works

```
your .am file → ast.parse (Python's own parser) → amlang/fixer.py (bug fixes) → compile → run
```

There is no custom parser, so the language stays small and compatible.
To add a new fix, add one `visit_*` method in `amlang/fixer.py` and a test in
`tests/test_fixes.py`.

## Tests

```bash
python -m unittest discover -s tests -v
node --test editors/vscode/test/extension.test.js
```

See [docs/ROADMAP.md](docs/ROADMAP.md) for the step-by-step plan.

## About

AM was created by **Anuj Mishra** (GitHub: [chaman640](https://github.com/chaman640)).
The goal: a language that is as easy to learn as possible, fits into the
Python world, and removes the Python mistakes that trip up beginners most.

## License

AM is free and open source under the [MIT License](LICENSE): anyone can use,
copy, change and share it, including for work.
