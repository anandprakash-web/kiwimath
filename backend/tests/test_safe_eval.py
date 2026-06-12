import pytest

from app.services.safe_eval import UnsafeExpressionError, safe_eval


def test_basic_arithmetic():
    assert safe_eval("N - K", {"N": 9, "K": 3}) == 6
    assert safe_eval("N + K", {"N": 9, "K": 3}) == 12
    assert safe_eval("N * 2", {"N": 5}) == 10
    assert safe_eval("N // 2", {"N": 7}) == 3


def test_comparisons_for_constraints():
    assert safe_eval("K < N", {"N": 9, "K": 3}) is True
    assert safe_eval("K < N", {"N": 3, "K": 9}) is False


def test_rejects_function_calls():
    with pytest.raises(UnsafeExpressionError):
        safe_eval("__import__('os').system('ls')", {})


def test_rejects_attribute_access():
    with pytest.raises(UnsafeExpressionError):
        safe_eval("N.__class__", {"N": 5})


def test_rejects_unknown_variable():
    with pytest.raises(UnsafeExpressionError, match="unknown variable"):
        safe_eval("X + 1", {"N": 5})


def test_pow_within_limits():
    assert safe_eval("2 ** 10", {}) == 1024
    assert safe_eval("N ** 2", {"N": 12}) == 144


def test_pow_guard_rejects_huge_exponent():
    with pytest.raises(UnsafeExpressionError, match="exponent"):
        safe_eval("2 ** 101", {})
    with pytest.raises(UnsafeExpressionError, match="exponent"):
        safe_eval("9 ** 999999", {})


def test_pow_guard_rejects_huge_base():
    with pytest.raises(UnsafeExpressionError, match="base"):
        safe_eval("1000001 ** 2", {})
    with pytest.raises(UnsafeExpressionError, match="base"):
        safe_eval("N ** 2", {"N": -2000000})
