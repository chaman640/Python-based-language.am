"""The bug fixes. Each visit_* method fixes one Python pitfall."""
import ast
import builtins
import copy

MISSING = "__am_missing__"

COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


class AmSyntaxError(SyntaxError):
    """A mistake AM finds before the program runs, with a hint to fix it."""

    def __init__(self, message, node, hint):
        super().__init__(message, (None, node.lineno, node.col_offset + 1, None))
        self.hint = hint


class Fixer(ast.NodeTransformer):
    def __init__(self):
        self.loop_vars = []   # one set of names per enclosing for-loop / comprehension
        self.func_depth = 0
        self.warnings = []    # (lineno, message) pairs, shown by compile_am

    # ------------------------------------------------------------ functions

    def visit_FunctionDef(self, node):
        check_outer_variable_change(node, nested=self.func_depth > 0)

        node.args = self.visit(node.args)
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        if node.returns:
            node.returns = self.visit(node.returns)
        saved, self.loop_vars = self.loop_vars, []   # outer loops don't apply inside
        self.func_depth += 1
        node.body = self.visit_statements(node.body)
        self.func_depth -= 1
        self.loop_vars = saved

        fix_mutable_defaults(node)
        return self.bind_loop_vars(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        node.args = self.visit(node.args)
        saved, self.loop_vars = self.loop_vars, []
        node.body = self.visit(node.body)
        self.loop_vars = saved
        return self.bind_loop_vars(node)

    # ------------------------------------------------------------ loops

    def visit_For(self, node):
        node.target = self.visit(node.target)
        node.iter = self.visit(node.iter)
        self.loop_vars.append(target_names(node.target))
        node.body = self.visit_statements(node.body)
        self.loop_vars.pop()
        node.orelse = self.visit_statements(node.orelse)
        return node

    visit_AsyncFor = visit_For

    def visit_comprehension_node(self, node):
        names = set()
        for gen in node.generators:
            names |= target_names(gen.target)
        self.loop_vars.append(names)
        self.generic_visit(node)
        self.loop_vars.pop()
        return node

    visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = visit_comprehension_node

    def visit_statements(self, body):
        new_body = []
        for stmt in body:
            result = self.visit(stmt)
            new_body.extend(result if isinstance(result, list) else [result])
        return new_body

    # Fix 5: functions made inside a loop remember the loop variable's value
    # at that moment (in Python they all see the last value).
    def bind_loop_vars(self, node):
        if not self.loop_vars:
            return node
        captured = sorted(set().union(*self.loop_vars) & free_names(node))
        if not captured:
            return node

        params = ast.arguments(
            posonlyargs=[], args=[ast.arg(arg=n) for n in captured], vararg=None,
            kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[],
        )
        current_values = [ast.Name(n, ast.Load()) for n in captured]

        if isinstance(node, ast.Lambda):
            # lambda: i   ->   (lambda i: (lambda: i))(i)
            return ast.Call(ast.Lambda(params, node), current_values, [])

        # def f(): ...   ->   def __am_bind_f(i):
        #                         def f(): ...
        #                         return f
        #                     f = __am_bind_f(i)
        #                     del __am_bind_f
        factory = f"__am_bind_{node.name}"
        make = ast.FunctionDef(
            name=factory, args=params, decorator_list=[], returns=None,
            body=[node, ast.Return(ast.Name(node.name, ast.Load()))],
        )
        if "type_params" in ast.FunctionDef._fields:
            make.type_params = []
        assign = ast.Assign(
            targets=[ast.Name(node.name, ast.Store())],
            value=ast.Call(ast.Name(factory, ast.Load()), current_values, []),
        )
        delete = ast.Delete([ast.Name(factory, ast.Del())])
        return [ast.copy_location(new, node) for new in (make, assign, delete)]

    # ------------------------------------------------------------ comparisons

    def visit_Compare(self, node):
        self.generic_visit(node)
        # Fix 2: `x is 5` / `x is "a"` -> `x == 5`  (`is None` stays as is)
        for i, (op, right) in enumerate(zip(node.ops, node.comparators)):
            if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(right, ast.Constant) and right.value is not None:
                node.ops[i] = ast.Eq() if isinstance(op, ast.Is) else ast.NotEq()

        # Fix 6: warn about `== 0.3` (decimal numbers are not stored exactly)
        if any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            if any(has_decimal_literal(part) for part in [node.left, *node.comparators]):
                self.warnings.append((
                    node.lineno,
                    "Comparing decimal numbers with == can give the wrong answer "
                    "(0.1 + 0.2 == 0.3 is False). Use math.isclose(a, b) instead.",
                ))
        return node

    # ------------------------------------------------------------ other fixes

    # Fix 3: bare `except:` -> `except Exception:` (Ctrl+C keeps working)
    def visit_ExceptHandler(self, node):
        self.generic_visit(node)
        if node.type is None:
            node.type = ast.Name("Exception", ast.Load())
        return node

    # Fix 4: overwriting built-ins (list = ..., print = ...) is an error
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and node.id in dir(builtins) and not node.id.startswith("_"):
            raise AmSyntaxError(
                f"'{node.id}' is a built-in name, choose another name",
                node,
                f"Python already uses '{node.id}'. Use another name, for example 'my_{node.id}'.",
            )
        return node


# Fix 1: mutable default arguments ([] {} set()) -> fresh copy on every call
def fix_mutable_defaults(node):
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


# Fix 7: `count += 1` inside a function, where `count` is never set in that
# function, always crashes in Python. Report it before the program runs.
def check_outer_variable_change(func, nested):
    bound = local_names(func, include_aug_assign=False)
    for node in walk_scope(func.body):
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name not in bound:
                keyword = "nonlocal" if nested else "global"
                raise AmSyntaxError(
                    f"'{name}' comes from outside this function and can't be changed here",
                    node,
                    f"Add '{keyword} {name}' as the first line of the function, "
                    f"or pass '{name}' in as an argument and return the new value.",
                )


# ---------------------------------------------------------------- helpers

def target_names(target):
    return {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}


def has_decimal_literal(expr):
    return any(
        isinstance(n, ast.Constant) and isinstance(n.value, float) and not n.value.is_integer()
        for n in ast.walk(expr)
    )


def walk_scope(body):
    """Walk the nodes of one scope, without entering nested functions or classes."""
    todo = list(body)
    while todo:
        node = todo.pop()
        yield node
        if isinstance(node, SCOPES):
            continue  # its name is bound here, its body is not
        for child in ast.iter_child_nodes(node):
            if isinstance(child, COMPREHENSIONS):
                # only walrus targets inside a comprehension bind in this scope
                todo.extend(n.target for n in ast.walk(child) if isinstance(n, ast.NamedExpr))
            else:
                todo.append(child)


def local_names(func, include_aug_assign=True):
    """Names that are local to a function or lambda (or declared global/nonlocal)."""
    args = func.args
    names = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
    names |= {a.arg for a in (args.vararg, args.kwarg) if a}
    body = [func.body] if isinstance(func, ast.Lambda) else func.body
    nodes = list(walk_scope(body))
    aug_targets = {id(n.target) for n in nodes if isinstance(n, ast.AugAssign)}
    for node in nodes:
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if include_aug_assign or id(node) not in aug_targets:
                names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names |= {(a.asname or a.name).split(".")[0] for a in node.names}
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names |= set(node.names)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif type(node).__name__ in ("MatchAs", "MatchStar") and getattr(node, "name", None):
            names.add(node.name)
        elif type(node).__name__ == "MatchMapping" and getattr(node, "rest", None):
            names.add(node.rest)
    return names


def free_names(func):
    """Names a function or lambda reads from outside itself."""
    body = [func.body] if isinstance(func, ast.Lambda) else func.body
    used = {
        n.id for stmt in body for n in ast.walk(stmt)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    return used - local_names(func)
