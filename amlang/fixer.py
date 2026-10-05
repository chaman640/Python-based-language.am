"""The bug fixes. Each visit_* method fixes one Python pitfall."""
import ast
import builtins
import copy

MISSING = "__am_missing__"


class Fixer(ast.NodeTransformer):
    # Fix 1: mutable default arguments ([] {} set()) -> fresh copy on every call
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        args = node.args
        params = args.posonlyargs + args.args
        pairs = list(zip(params[len(params) - len(args.defaults):], args.defaults))
        pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d]
        checks = []
        for arg, default in pairs:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                fresh = copy.deepcopy(default)
                default.__class__, default.__dict__ = ast.Name, {"id": MISSING, "ctx": ast.Load()}
                check = ast.parse(f"if {arg.arg} is {MISSING}: {arg.arg} = None").body[0]
                check.body[0].value = fresh
                checks.append(check)
        node.body = checks + node.body
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    # Fix 2: `x is 5` / `x is "a"` -> `x == 5`  (`is None` stays as is)
    def visit_Compare(self, node):
        self.generic_visit(node)
        for i, (op, right) in enumerate(zip(node.ops, node.comparators)):
            if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(right, ast.Constant) and right.value is not None:
                node.ops[i] = ast.Eq() if isinstance(op, ast.Is) else ast.NotEq()
        return node

    # Fix 3: bare `except:` -> `except Exception:` (Ctrl+C keeps working)
    def visit_ExceptHandler(self, node):
        self.generic_visit(node)
        if node.type is None:
            node.type = ast.Name("Exception", ast.Load())
        return node

    # Fix 4: overwriting built-ins (list = ..., print = ...) is an error
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and node.id in dir(builtins) and not node.id.startswith("_"):
            raise SyntaxError(
                f"'{node.id}' is a built-in name, choose another name",
                (None, node.lineno, node.col_offset + 1, None),
            )
        return node
