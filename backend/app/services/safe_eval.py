"""
Safe arithmetic evaluator for Kiwimath.

Why not `eval()`? Authored questions come from trusted content creators, but
we still don't want `__import__('os').system(...)` to be even theoretically
possible in a question formula. This evaluator uses Python's AST and allows
only arithmetic operators and variable lookups.

Supported:
    +, -, *, /, //, %, **, unary minus
    variable names from the provided context
    integer / float / string literals
    ternary expressions (a if cond else b)
    boolean operators (and, or, not)
    comparisons (<, <=, >, >=, ==, !=)

Anything else raises UnsafeExpressionError.

Examples:
    >>> safe_eval("N - K", {"N": 9, "K": 3})
    6
    >>> safe_eval("N + K * 2", {"N": 5, "K": 3})
    11
    >>> safe_eval("K < N", {"N": 9, "K": 3})
    True
    >>> safe_eval("'Triangle' if N==3 else 'Square'", {"N": 3})
    'Triangle'
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
    ast.Not: lambda a: not a,
}

_ALLOWED_COMPARES = {
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
}


def _reverse_digits(n: int) -> int:
    """Reverse the digits of a positive integer (e.g. 35 → 53)."""
    return int(str(abs(int(n)))[::-1])


def _mirror(n: int) -> int:
    """Mirror / reverse digits — alias for reverse_digits."""
    return _reverse_digits(n)


def _fewest_coins(total: int) -> int:
    """Minimum coins to make `total` cents using 1, 5, 10, 25 denominations."""
    coins = 0
    for d in (25, 10, 5, 1):
        coins += total // d
        total %= d
    return coins


def _compare(a, b) -> str:
    """Return '>' / '<' / '=' comparing a and b."""
    if a > b:
        return ">"
    elif a < b:
        return "<"
    return "="


def _lcm(a: int, b: int) -> int:
    """Least common multiple of two integers."""
    import math
    return abs(a * b) // math.gcd(a, b)


def _gcd(a: int, b: int) -> int:
    """Greatest common divisor."""
    import math
    return math.gcd(int(a), int(b))


def _combinations(n: int, r: int) -> int:
    """C(n, r) — binomial coefficient."""
    import math
    return math.comb(int(n), int(r))


def _round_val(x, ndigits=0) -> Number:
    """Round a number. round(x) or round(x, ndigits)."""
    return round(x, int(ndigits))


# Thread-local RNG for random_int/random_choice in derived rules.
import random as _random
_derived_rng = _random.Random()

def _random_int(a: int, b: int) -> int:
    """Random integer in [a, b] inclusive."""
    return _derived_rng.randint(int(a), int(b))


def _random_choice(*args) -> Any:
    """Pick one of the arguments at random."""
    return _derived_rng.choice(list(args))


def _sorted_list(lst, reverse=False):
    """Sort a list, optionally in reverse."""
    if isinstance(lst, (list, tuple)):
        return sorted(lst, reverse=bool(reverse))
    return lst

def _sqrt(x):
    """Integer square root if perfect, else float."""
    import math
    result = math.isqrt(int(x)) if isinstance(x, int) and x >= 0 else x ** 0.5
    if isinstance(x, int) and result * result == x:
        return result
    return x ** 0.5

def _count_factors(n):
    """Count all factors of n."""
    n = int(abs(n))
    if n == 0:
        return 0
    return sum(1 for i in range(1, n + 1) if n % i == 0)

def _digit_in_place(n, place):
    """Get digit at given place value (0=ones, 1=tens, 2=hundreds)."""
    return int(abs(int(n))) // (10 ** int(place)) % 10

def _factorial(n):
    """Factorial of n."""
    import math
    return math.factorial(int(n))

def _prime_factors(n):
    """Return list of prime factors."""
    n = int(abs(n))
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def _is_prime(n):
    """Check if n is prime."""
    n = int(abs(n))
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def _sum_digits(n):
    """Sum of digits of n."""
    return sum(int(d) for d in str(abs(int(n))))


def _floor(x):
    """Floor of a number."""
    import math
    return math.floor(x)

def _ceil(x):
    """Ceiling of a number."""
    import math
    return math.ceil(x)

def _digit_at(n, place):
    """Get digit at a named place: 0=ones, 1=tens, 2=hundreds, etc.
    Also accepts string place names."""
    place_map = {
        'ones': 0, 'units': 0,
        'tens': 1,
        'hundreds': 2,
        'thousands': 3,
        'ten_thousands': 4, 'tenths': -1,
        'hundredths': -2, 'thousandths': -3,
    }
    if isinstance(place, str):
        place = place_map.get(place.lower(), 0)
    place = int(place)
    if place < 0:
        # Decimal places
        s = str(float(n))
        dot = s.index('.')
        idx = dot - place
        if idx < len(s):
            return int(s[idx])
        return 0
    return int(abs(int(float(n)))) // (10 ** place) % 10

def _count_factor_pairs(n):
    """Count factor pairs of n (e.g. 12 has pairs (1,12),(2,6),(3,4) = 3)."""
    n = int(abs(n))
    if n == 0:
        return 0
    count = 0
    i = 1
    while i * i <= n:
        if n % i == 0:
            count += 1
        i += 1
    return count

def _prime_factorization(n):
    """Return prime factorization as a string like '2^2 x 3'."""
    n = int(abs(n))
    if n <= 1:
        return str(n)
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    parts = []
    for p in sorted(factors):
        if factors[p] == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{factors[p]}")
    return " x ".join(parts)

def _argmin(*args):
    """Return the index of the minimum value (0-based)."""
    return min(range(len(args)), key=lambda i: args[i])

def _lookup(key, *args):
    """Simple lookup - returns the key itself (used as passthrough)."""
    return key


_ALLOWED_FUNCTIONS: Dict[str, Any] = {
    "max": max,
    "min": min,
    "abs": abs,
    "round": _round_val,
    "int": int,
    "len": len,
    "reverse_digits": _reverse_digits,
    "mirror": _mirror,
    "fewest_coins": _fewest_coins,
    "compare": _compare,
    "lcm": _lcm,
    "gcd": _gcd,
    "C": _combinations,
    "comb": _combinations,
    "random_int": _random_int,
    "random_choice": _random_choice,
    "sorted": _sorted_list,
    "sqrt": _sqrt,
    "count_factors": _count_factors,
    "digit_in_place": _digit_in_place,
    "factorial": _factorial,
    "prime_factors": _prime_factors,
    "is_prime": _is_prime,
    "sum_digits": _sum_digits,
    "str": str,
    "float": float,
    "floor": _floor,
    "ceil": _ceil,
    "digit_at": _digit_at,
    "digit_at_place": _digit_at,
    "count_factor_pairs": _count_factor_pairs,
    "prime_factorization": _prime_factorization,
    "argmin": _argmin,
    "lookup": _lookup,
}


def _evaluate(node: ast.AST, ctx: Dict[str, Any]) -> Any:
    # Literal (3, 3.14, "hello")
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, str, bool)):
            return node.value
        raise UnsafeExpressionError(
            f"only numeric/string/bool constants allowed, got {type(node.value).__name__}"
        )

    # Variable lookup (N, K, K_small)
    if isinstance(node, ast.Name):
        # Check allowed functions first (for cases like ``abs`` without call)
        if node.id in ctx:
            return ctx[node.id]
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        raise UnsafeExpressionError(f"unknown variable '{node.id}'")

    # Function call: max(A, B), min(A, B, C), abs(X), etc.
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            fn = _ALLOWED_FUNCTIONS.get(node.func.id)
            if fn is None:
                raise UnsafeExpressionError(
                    f"function '{node.func.id}' not allowed"
                )
            args = [_evaluate(a, ctx) for a in node.args]
            kwargs = {}
            for kw in node.keywords:
                if kw.arg is None:
                    raise UnsafeExpressionError("**kwargs not allowed")
                kwargs[kw.arg] = _evaluate(kw.value, ctx)
            return fn(*args, **kwargs)
        raise UnsafeExpressionError("only named function calls allowed")

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

    # Ternary expression (a if cond else b)
    if isinstance(node, ast.IfExp):
        condition = _evaluate(node.test, ctx)
        if condition:
            return _evaluate(node.body, ctx)
        return _evaluate(node.orelse, ctx)

    # Boolean operators (and, or)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = _evaluate(value, ctx)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _evaluate(value, ctx)
                if result:
                    return result
            return result
        raise UnsafeExpressionError(f"boolean op {type(node.op).__name__} not allowed")

    # Unary not
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _evaluate(node.operand, ctx)

    # Subscript — support list/tuple indexing: values[0], etc.
    if isinstance(node, ast.Subscript):
        obj = _evaluate(node.value, ctx)
        if isinstance(node.slice, ast.Constant):
            idx = node.slice.value
        else:
            idx = _evaluate(node.slice, ctx)
        return obj[idx]

    # List literal: [1, 2, 3]
    if isinstance(node, ast.List):
        return [_evaluate(elt, ctx) for elt in node.elts]

    # Tuple literal: (1, 2)
    if isinstance(node, ast.Tuple):
        return tuple(_evaluate(elt, ctx) for elt in node.elts)

    raise UnsafeExpressionError(f"AST node {type(node).__name__} not allowed")


def safe_eval(expression: str, context: Dict[str, Any]) -> Any:
    """Evaluate an arithmetic/comparison expression against a variable context."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise UnsafeExpressionError(f"invalid expression '{expression}': {e}") from e
    return _evaluate(tree.body, context)
