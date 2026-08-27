"""Safe evaluation of ``<if>`` / ``<elif>`` conditions.

Conditions come from template text, which is not necessarily trusted, so they are
walked over an allowlist of AST nodes instead of being handed to ``eval``.
Anything not listed here — calls, attribute access, imports, comprehensions — is
rejected rather than executed.
"""

import ast
import operator


class ConditionError(Exception):
    """A condition is malformed, unsupported, or references an unknown name."""


class UnknownNameError(ConditionError):
    """A condition references a name absent from the context.

    Kept separate because an optional context variable is normal usage, while the
    other ConditionError cases indicate a mistake in the template.
    """


_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}

# ``**`` is deliberately absent: it makes tiny expressions arbitrarily expensive.
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def evaluate_condition(expression, context):
    """Evaluate ``expression`` against ``context`` and return its truth value."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ConditionError(f"Invalid condition: {expression!r}") from error
    return bool(_evaluate(tree.body, context))


def _evaluate(node, context):
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id not in context:
            raise UnknownNameError(f"Unknown name in condition: {node.id!r}")
        return context[node.id]

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = _evaluate(value, context)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = _evaluate(value, context)
            if result:
                return result
        return result

    if isinstance(node, ast.UnaryOp):
        handler = _UNARY_OPS.get(type(node.op))
        if handler is None:
            raise ConditionError(f"Unsupported operator: {type(node.op).__name__}")
        return _apply(handler, _evaluate(node.operand, context))

    if isinstance(node, ast.BinOp):
        handler = _BINARY_OPS.get(type(node.op))
        if handler is None:
            raise ConditionError(f"Unsupported operator: {type(node.op).__name__}")
        left = _evaluate(node.left, context)
        right = _evaluate(node.right, context)
        return _apply(handler, left, right)

    if isinstance(node, ast.Compare):
        left = _evaluate(node.left, context)
        for op, comparator_node in zip(node.ops, node.comparators):
            handler = _COMPARE_OPS.get(type(op))
            if handler is None:
                raise ConditionError(f"Unsupported operator: {type(op).__name__}")
            right = _evaluate(comparator_node, context)
            if not _apply(handler, left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Subscript):
        value = _evaluate(node.value, context)
        key = _evaluate(node.slice, context)
        try:
            return value[key]
        except (KeyError, IndexError, TypeError) as error:
            raise ConditionError(f"Cannot index value with {key!r}") from error

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_evaluate(element, context) for element in node.elts]

    raise ConditionError(f"Unsupported expression: {type(node).__name__}")


def _apply(handler, *operands):
    try:
        return handler(*operands)
    except ConditionError:
        raise
    except Exception as error:
        raise ConditionError(str(error)) from error
