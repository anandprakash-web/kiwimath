"""
Safe arithmetic evaluator for Kiwimath.

Why not `eval()`? Authored questions come from trusted content creators, but
we still don't want `__import__('os').system(...)` to be even theoretically
possible in a question formula. This evaluator uses Python's AST and allows
only arithmetic operators and variable lookups.

Supported:
    +, -, *, /, //, %, **, unary minus
    variable names from the provided context
    integer / float literals

Anything else raises UnsafeExpressionError.

Examples:
    >>> safe_eval("N - K", {"N": 9, "K": 3})
    6
    >>> safe_eval("N + K * 2", {"N": 5, "K": 3})
    11
    >>> safe_eval("K < N", {"N": 9, "K": 3})
    True
"""

from __future__ import annotations

import ast
from typing import Any, Dict, Union


class UnsafeExpressionError(ValueError):
    """Raised when a formula contains something we can't evaluate safely."""


Number = Union[int, float]


_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}

_ALLOWED_UNARYOPS = {
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: +a,
}

_ALLOWED_COMPARES = {
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
}


def _evaluate(node: ast.AST, ctx: Dict[str, Any]) -> Any:
    # Numeric literal (3, 3.14)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise UnsafeExpressionError(
            f"only numeric constants allowed, got {type(node.value).__name__}"
        )

    # Variable lookup (N, K, K_small)
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise UnsafeExpressionError(f"unknown variable '{node.id}'")
        return ctx[node.id]

    # Binary op (a + b)
    if isinstance(node, ast.BinOp):
        op_fn = _ALLOWED_BINOPS.get(type(node.op))
        if op_fn is None:
            raise UnsafeExpressionError(
                f"operator {type(node.op).__name__} not allowed"
            )
        return op_fn(_evaluate(node.left, ctx), _evaluate(node.right, ctx))

    # Unary op (-a)
    if isinstance(node, ast.UnaryOp):
        op_fn = _ALLOWED_UNARYOPS.get(type(node.op))
        if op_fn is None:
            raise UnsafeExpressionError(
                f"unary operator {type(node.op).__name__} not allowed"
            )
        return op_fn(_evaluate(node.operand, ctx))

    # Comparison (a < b) — used by param constraints
    if isinstance(node, ast.Compare):
        # Python allows chained comparisons like `1 < a < 10`. Evaluate all pairs.
        left = _evaluate(node.left, ctx)
        for op, right_node in zip(node.ops, node.comparators):
            op_fn = _ALLOWED_COMPARES.get(type(op))
            if op_fn is None:
                raise UnsafeExpressionError(
                    f"comparison {type(op).__name__} not allowed"
                )
            right = _evaluate(right_node, ctx)
            if not op_fn(left, right):
                return False
            left = right
        return True

    raise UnsafeExpressionError(f"AST node {type(node).__name__} not allowed")


def safe_eval(expression: str, context: Dict[str, Any]) -> Any:
    """Evaluate an arithmetic/comparison expression against a variable context."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise UnsafeExpressionError(f"invalid expression '{expression}': {e}") from e
    return _evaluate(tree.body, context)
