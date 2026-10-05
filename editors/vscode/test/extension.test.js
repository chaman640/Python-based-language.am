// Runs extension.js against a small fake `vscode` module and the real `am`
// command, so the editor behaviour is tested without opening VS Code.
// Run with: node --test test/extension.test.js
const test = require("node:test");
const assert = require("node:assert");
const Module = require("module");

const listeners = {};
const commands = {};
const diagnosticsSet = new Map();
const sentToTerminal = [];
const fakeVscode = {
  Range: class {
    constructor(sl, sc, el, ec) {
      Object.assign(this, { sl, sc, el, ec });
    }
  },
  Diagnostic: class {
    constructor(range, message, severity) {
      Object.assign(this, { range, message, severity });
    }
  },
  DiagnosticSeverity: { Error: 0, Warning: 1 },
  languages: {
    createDiagnosticCollection: () => ({
      set: (uri, list) => diagnosticsSet.set(uri.toString(), list),
      delete: (uri) => diagnosticsSet.delete(uri.toString()),
      dispose() {},
    }),
  },
  workspace: {
    textDocuments: [],
    getConfiguration: () => ({ get: (key, fallback) => fallback }),
    onDidOpenTextDocument: (fn) => (listeners.open = fn),
    onDidSaveTextDocument: (fn) => (listeners.save = fn),
    onDidChangeTextDocument: (fn) => (listeners.change = fn),
    onDidCloseTextDocument: (fn) => (listeners.close = fn),
  },
  window: {
    terminals: [],
    activeTextEditor: undefined,
    createTerminal: (name) => ({ name, show() {}, sendText: (t) => sentToTerminal.push(t) }),
    showInformationMessage() {},
    showWarningMessage: () => Promise.resolve(),
  },
  commands: {
    registerCommand: (name, fn) => (commands[name] = fn),
    executeCommand() {},
  },
};

const originalLoad = Module._load;
Module._load = function (request, ...rest) {
  return request === "vscode" ? fakeVscode : originalLoad.call(this, request, ...rest);
};
const extension = require("../extension.js");
extension.activate({ subscriptions: [] });

function fakeDocument(name, text) {
  const lines = text.split("\n");
  return {
    languageId: "am",
    version: 1,
    isUntitled: false,
    uri: { scheme: "file", fsPath: `/tmp/${name}`, toString: () => `file:///tmp/${name}` },
    lineCount: lines.length,
    getText: () => text,
    save: async () => true,
    lineAt: (i) => ({
      text: lines[i],
      firstNonWhitespaceCharacterIndex: lines[i].length - lines[i].trimStart().length,
    }),
  };
}

function waitForDiagnostics(document) {
  const key = document.uri.toString();
  return new Promise((resolve, reject) => {
    const started = Date.now();
    (function poll() {
      if (diagnosticsSet.has(key)) return resolve(diagnosticsSet.get(key));
      if (Date.now() - started > 15000) return reject(new Error("no diagnostics"));
      setTimeout(poll, 50);
    })();
  });
}

test("shows an error with its hint on the right line", async () => {
  const doc = fakeDocument("outer.am", "count = 0\ndef inc():\n    count += 1\n");
  listeners.open(doc);
  const [d] = await waitForDiagnostics(doc);
  assert.strictEqual(d.severity, fakeVscode.DiagnosticSeverity.Error);
  assert.strictEqual(d.range.sl, 2);
  assert.strictEqual(d.range.sc, 4);
  assert.match(d.message, /'count' comes from outside this function/);
  assert.match(d.message, /Hint: Add 'global count'/);
});

test("shows decimal == as a warning", async () => {
  const doc = fakeDocument("decimal.am", "total = 0.1 + 0.2\nprint(total == 0.3)\n");
  listeners.open(doc);
  const [d] = await waitForDiagnostics(doc);
  assert.strictEqual(d.severity, fakeVscode.DiagnosticSeverity.Warning);
  assert.strictEqual(d.range.sl, 1);
  assert.match(d.message, /math\.isclose/);
});

test("underlines the whole line for a missing ':' at the end", async () => {
  const doc = fakeDocument("colon.am", "if True\n    print(1)\n");
  listeners.open(doc);
  const [d] = await waitForDiagnostics(doc);
  assert.deepStrictEqual([d.range.sl, d.range.sc, d.range.ec], [0, 0, 7]);
  assert.match(d.message, /missing ':'/);
});

test("clean code has no problems", async () => {
  const doc = fakeDocument("clean.am", "print('hello')\n");
  listeners.open(doc);
  assert.deepStrictEqual(await waitForDiagnostics(doc), []);
});

test("Run button runs the file with am in a terminal", async () => {
  const doc = fakeDocument("hello.am", "print('hi')\n");
  fakeVscode.window.activeTextEditor = { document: doc };
  await commands["am.runFile"]();
  assert.deepStrictEqual(sentToTerminal, ['am "/tmp/hello.am"']);
});
