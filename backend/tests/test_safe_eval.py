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
