# AM Language for VS Code

- **Colours** for `.am` files (the same as Python)
- **Auto-indent** after `:`, comment toggling with `Ctrl+/`, bracket and quote pairs
- **Errors and warnings while you type**, with the same hints `am` prints
- **Run button** (▶ at the top right) runs the file with `am` in a terminal

The extension uses the `am` command, so install AM first:

```bash
cd Python-based-language.am
pip install -e .
```

## Install the extension

**Option 1: from a .vsix file (recommended)**

1. Download `am-language.vsix` from the latest
   [tests run on GitHub Actions](https://github.com/chaman640/Python-based-language.am/actions)
   (open the run, scroll to *Artifacts*, download and unzip `am-language-vsix`),
   or build it yourself:
   ```bash
   cd editors/vscode
   npx @vscode/vsce package
   ```
2. In VS Code: Extensions panel → `...` menu → **Install from VSIX...** → pick the file.
   Or from a terminal: `code --install-extension am-language-0.1.0.vsix`

**Option 2: only colours, no extension**

Add this to your VS Code `settings.json`:

```json
"files.associations": { "*.am": "python" }
```

You get Python colours, but not the AM errors, hints, or Run button.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `am.command` | `am` | Command used to run and check files, e.g. `python -m amlang` |
| `am.checkWhileTyping` | `true` | Check while typing; if off, only on open and save |

## Develop

Open this folder in VS Code and press `F5` to start a window with the extension loaded.
Tests (no VS Code needed): `node --test test/extension.test.js`
