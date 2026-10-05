// VS Code support for AM: errors/warnings while typing, and a Run button.
// The checking itself is done by `am --check --json -`, so the editor always
// agrees with what `am` would say.
const vscode = require("vscode");
const { execFile } = require("child_process");
const path = require("path");

const DELAY_MS = 400;

function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection("am");
  const timers = new Map();
  let warnedMissing = false;

  const settings = () => vscode.workspace.getConfiguration("am");
  const commandParts = () => settings().get("command", "am").trim().split(/\s+/);

  function check(document) {
    if (document.languageId !== "am") return;
    const [exe, ...prefix] = commandParts();
    const version = document.version;
    const cwd = document.uri.scheme === "file" ? path.dirname(document.uri.fsPath) : undefined;

    const child = execFile(
      exe,
      [...prefix, "--check", "--json", "-"],
      { cwd, timeout: 10000 },
      (error, stdout) => {
        if (document.version !== version) return; // a newer check is on its way
        let problems;
        try {
          problems = JSON.parse(stdout);
        } catch (e) {
          if (error && error.code === "ENOENT") showMissing(exe);
          return;
        }
        diagnostics.set(document.uri, problems.map((p) => toDiagnostic(document, p)));
      }
    );
    child.on("error", () => {}); // reported through the callback above
    child.stdin.on("error", () => {});
    child.stdin.end(document.getText());
  }

  function showMissing(exe) {
    if (warnedMissing) return;
    warnedMissing = true;
    vscode.window
      .showWarningMessage(
        `AM: could not run "${exe}". Install AM with "pip install -e ." in the AM folder, or set "am.command".`,
        "Open Settings"
      )
      .then((choice) => {
        if (choice) vscode.commands.executeCommand("workbench.action.openSettings", "am.command");
      });
  }

  function scheduleCheck(document) {
    if (document.languageId !== "am") return;
    const key = document.uri.toString();
    clearTimeout(timers.get(key));
    timers.set(key, setTimeout(() => check(document), DELAY_MS));
  }

  context.subscriptions.push(
    diagnostics,
    vscode.workspace.onDidOpenTextDocument(check),
    vscode.workspace.onDidSaveTextDocument(check),
    vscode.workspace.onDidChangeTextDocument((event) => {
      if (settings().get("checkWhileTyping", true)) scheduleCheck(event.document);
    }),
    vscode.workspace.onDidCloseTextDocument((document) => diagnostics.delete(document.uri)),
    vscode.commands.registerCommand("am.checkFile", () => {
      const editor = vscode.window.activeTextEditor;
      if (editor) check(editor.document);
    }),
    vscode.commands.registerCommand("am.runFile", (uri) => runFile(uri, commandParts()))
  );

  vscode.workspace.textDocuments.forEach(check);
}

async function runFile(uri, parts) {
  const editor = vscode.window.activeTextEditor;
  const document = uri
    ? await vscode.workspace.openTextDocument(uri)
    : editor && editor.document;
  if (!document || document.languageId !== "am") {
    vscode.window.showInformationMessage("AM: open a .am file to run it.");
    return;
  }
  if (document.isUntitled) {
    vscode.window.showInformationMessage("AM: save the file first, then run it.");
    return;
  }
  await document.save();

  let terminal = vscode.window.terminals.find((t) => t.name === "AM");
  if (!terminal) terminal = vscode.window.createTerminal("AM");
  terminal.show();
  terminal.sendText(`${parts.join(" ")} "${document.uri.fsPath}"`);
}

function toDiagnostic(document, problem) {
  const lineNo = Math.min(Math.max(problem.line - 1, 0), document.lineCount - 1);
  const line = document.lineAt(lineNo);
  const firstChar = line.firstNonWhitespaceCharacterIndex;
  const start = Math.max(firstChar, Math.min((problem.column || 1) - 1, line.text.length));
  let end = line.text.length;
  if (problem.end_line === problem.line && problem.end_column && problem.end_column - 1 > start) {
    end = Math.min(problem.end_column - 1, line.text.length);
  }
  const range =
    start < end
      ? new vscode.Range(lineNo, start, lineNo, end)
      : new vscode.Range(lineNo, firstChar, lineNo, line.text.length); // e.g. missing ':' at end of line

  const message = problem.hint ? `${problem.message}\nHint: ${problem.hint}` : problem.message;
  const severity =
    problem.severity === "error"
      ? vscode.DiagnosticSeverity.Error
      : vscode.DiagnosticSeverity.Warning;
  const diagnostic = new vscode.Diagnostic(range, message, severity);
  diagnostic.source = "am";
  return diagnostic;
}

function deactivate() {}

module.exports = { activate, deactivate, toDiagnostic };
