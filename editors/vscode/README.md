# AM Language for VS Code

Support for **AM**, a free programming language created by **Anuj Mishra**.
AM looks exactly like Python, runs every Python library, and fixes common
Python bugs automatically. Files end in `.am`.

## Features

- **Colours** for `.am` files (the same as Python)
- **Errors and warnings while you type**, with an easy hint on how to fix each one
- **▶ Run button** (top right of the editor) runs the file with `am` in a terminal
- **Auto-indent** after `:`, comment toggling with `Ctrl+/`, bracket and quote pairs

```
Error in main.am, line 2:
    print(nmae)

NameError: name 'nmae' is not defined
Hint: Did you mean 'name'?
```

## Getting started

1. Install AM (needs Python 3.9 or newer):
   ```bash
   pip install am-language
   ```
2. Install this extension.
3. Create a file `hello.am`:
   ```python
   name = "World"
   print("Hello " + name)
   ```
4. Press ▶ at the top right.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `am.command` | `am` | Command used to run and check files, e.g. `python -m amlang` |
| `am.checkWhileTyping` | `true` | Check while typing; if off, only on open and save |

## Install without the Marketplace

Download `am-language-<version>.vsix` from the
[GitHub releases](https://github.com/chaman640/Python-based-language.am/releases), then in VS Code:
Extensions panel → `...` menu → **Install from VSIX...**

## About

AM and this extension were created by **Anuj Mishra**
([GitHub: chaman640](https://github.com/chaman640)) and are free and open source
under the MIT License.

- Website: https://chaman640.github.io/Python-based-language.am/
- Code: https://github.com/chaman640/Python-based-language.am
- Python package: https://pypi.org/project/am-language/

## Develop

Open this folder in VS Code and press `F5` to start a window with the extension loaded.
Tests (no VS Code needed): `node --test test/extension.test.js`
