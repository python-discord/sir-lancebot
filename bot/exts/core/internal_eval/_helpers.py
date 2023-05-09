import ast
import collections
import contextlib
import functools
import inspect
import io
import logging
import sys
import traceback
import types
from typing import Any

log = logging.getLogger(__name__)

# A type alias to annotate the tuples returned from `sys.exc_info()`
ExcInfo = tuple[type[Exception], Exception, types.TracebackType]
Namespace = dict[str, Any]

# This will be used as an coroutine function wrapper for the code
# to be evaluated. The wrapper contains one `pass` statement which
# will be replaced with `ast` with the code that we want to have
# evaluated.
# The function redirects output and captures exceptions that were
# raised in the code we evaluate. The latter is used to provide a
# meaningful traceback to the end user.
EVAL_WRAPPER = """
async def _eval_wrapper_function():
    try:
        with contextlib.redirect_stdout(_eval_context.stdout):
            pass
        if '_value_last_expression' in locals():
            if inspect.isawaitable(_value_last_expression):
                _value_last_expression = await _value_last_expression
            _eval_context._value_last_expression = _value_last_expression
        else:
            _eval_context._value_last_expression = None
    except Exception:
        _eval_context.exc_info = sys.exc_info()
    finally:
        _eval_context.locals = locals()
_eval_context.function = _eval_wrapper_function
"""
INTERNAL_EVAL_FRAMENAME = "<internal eval>"
EVAL_WRAPPER_FUNCTION_FRAMENAME = "_eval_wrapper_function"


def format_internal_eval_exception(exc_info: ExcInfo, code: str) -> str:
    """Format an exception caught while evaluation code by inserting lines."""
    exc_type, exc_value, tb = exc_info
    stack_summary = traceback.StackSummary.extract(traceback.walk_tb(tb))
    code = code.split("\n")

    output = ["Traceback (most recent call last):"]
    for frame in stack_summary:
        if frame.filename == INTERNAL_EVAL_FRAMENAME:
            line = code[frame.lineno - 1].lstrip()

            if frame.name == EVAL_WRAPPER_FUNCTION_FRAMENAME:
                name = INTERNAL_EVAL_FRAMENAME
            else:
                name = frame.name
        else:
            line = frame.line
            name = frame.name

        output.append(
            f'  File "{frame.filename}", line {frame.lineno}, in {name}\n'
            f"    {line}"
        )

    output.extend(traceback.format_exception_only(exc_type, exc_value))
    return "\n".join(output)


class EvalContext:
    """
    Represents the current `internal eval` context.

    The context remembers names set during earlier runs of `internal eval`. To
    clear the context, use the `.internal clear` command.
    """

    def __init__(self, context_vars: Namespace, local_vars: Namespace):
        self._locals = dict(local_vars)
        self.context_vars = dict(context_vars)

        self.stdout = io.StringIO()
        self._value_last_expression = None
        self.exc_info = None
        self.code = ""
        self.function = None
        self.eval_tree = None

    @property
    def dependencies(self) -> dict[str, Any]:
        """
        Return a mapping of the dependencies for the wrapper function.

        By using a property descriptor, the mapping can't be accidentally
        mutated during evaluation. This ensures the dependencies are always
        available.
        """
        return {
            "print": functools.partial(print, file=self.stdout),
            "contextlib": contextlib,
            "inspect": inspect,
            "sys": sys,
            "_eval_context": self,
            "_": self._value_last_expression,
        }

    @property
    def locals(self) -> dict[str, Any]:
        """Return a mapping of names->values needed for evaluation."""
        return {**collections.ChainMap(self.dependencies, self.context_vars, self._locals)}

    @locals.setter
    def locals(self, locals_: dict[str, Any]) -> None:
        """Update the contextual mapping of names to values."""
        log.trace(f"Updating {self._locals} with {locals_}")
        self._locals.update(locals_)

    def prepare_eval(self, code: str) -> str | None:
        """Prepare an evaluation by processing the code and setting up the context."""
        self.code = code

        if not self.code:
            log.debug("No code was attached to the evaluation command")
            return "[No code detected]"

        try:
            code_tree = ast.parse(code, filename=INTERNAL_EVAL_FRAMENAME)
        except SyntaxError:
            log.debug("Got a SyntaxError while parsing the eval code")
            return "".join(traceback.format_exception(*sys.exc_info(), limit=0))

        log.trace("Parsing the AST to see if there's a trailing expression we need to capture")
        code_tree = CaptureLastExpression(code_tree).capture()

        log.trace("Wrapping the AST in the AST of the wrapper coroutine")
        eval_tree = WrapEvalCodeTree(code_tree).wrap()

        self.eval_tree = eval_tree
        return None

    async def run_eval(self) -> Namespace:
        """Run the evaluation and return the updated locals."""
        log.trace("Compiling the AST to bytecode using `exec` mode")
        compiled_code = compile(self.eval_tree, filename=INTERNAL_EVAL_FRAMENAME, mode="exec")

        log.trace("Executing the compiled code with the desired namespace environment")
        exec(compiled_code, self.locals)  # noqa: S102

        log.trace("Awaiting the created evaluation wrapper coroutine.")
        await self.function()

        log.trace("Returning the updated captured locals.")
        return self._locals

    def format_output(self) -> str:
        """Format the output of the most recent evaluation."""
        output = []

        log.trace(f"Getting output from stdout `{id(self.stdout)}`")
        stdout_text = self.stdout.getvalue()
        if stdout_text:
            log.trace("Appending output captured from stdout/print")
            output.append(stdout_text)

        if self._value_last_expression is not None:
            log.trace("Appending the output of a captured trialing expression")
            output.append(f"[Captured] {self._value_last_expression!r}")

        if self.exc_info:
            log.trace("Appending exception information")
            output.append(format_internal_eval_exception(self.exc_info, self.code))

        log.trace(f"Generated output: {output!r}")
        return "\n".join(output) or "[No output]"


class WrapEvalCodeTree(ast.NodeTransformer):
    """Wraps the AST of eval code with the wrapper function."""

    def __init__(self, eval_code_tree: ast.AST, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_code_tree = eval_code_tree

        # To avoid mutable aliasing, parse the WRAPPER_FUNC for each wrapping
        self.wrapper = ast.parse(EVAL_WRAPPER, filename=INTERNAL_EVAL_FRAMENAME)

    def wrap(self) -> ast.AST:
        """Wrap the tree of the code by the tree of the wrapper function."""
        new_tree = self.visit(self.wrapper)
        return ast.fix_missing_locations(new_tree)

    def visit_Pass(self, node: ast.Pass) -> list[ast.AST]:  # noqa: N802
        """
        Replace the `_ast.Pass` node in the wrapper function by the eval AST.

        This method works on the assumption that there's a single `pass`
        statement in the wrapper function.
        """
        return list(ast.iter_child_nodes(self.eval_code_tree))


class CaptureLastExpression(ast.NodeTransformer):
    """Captures the return value from a loose expression."""

    def __init__(self, tree: ast.AST, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = tree
        self.last_node = list(ast.iter_child_nodes(tree))[-1]

    def visit_Expr(self, node: ast.Expr) -> ast.Expr | ast.Assign:  # noqa: N802
        """
        Replace the Expr node that is last child node of Module with an assignment.

        We use an assignment to capture the value of the last node, if it's a loose
        Expr node. Normally, the value of an Expr node is lost, meaning we don't get
        the output of such a last "loose" expression. By assigning it a name, we can
        retrieve it for our output.
        """
        if node is not self.last_node:
            return node

        log.trace("Found a trailing last expression in the evaluation code")

        log.trace("Creating assignment statement with trailing expression as the right-hand side")
        right_hand_side = list(ast.iter_child_nodes(node))[0]

        assignment = ast.Assign(
            targets=[ast.Name(id="_value_last_expression", ctx=ast.Store())],
            value=right_hand_side,
            lineno=node.lineno,
            col_offset=0,
        )
        ast.fix_missing_locations(assignment)
        return assignment

    def capture(self) -> ast.AST:
        """Capture the value of the last expression with an assignment."""
        if not isinstance(self.last_node, ast.Expr):
            # We only have to replace a node if the very last node is an Expr node
            return self.tree

        new_tree = self.visit(self.tree)
        return ast.fix_missing_locations(new_tree)
