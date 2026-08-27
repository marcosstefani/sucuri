"""Conditions must never execute template-supplied code (see sucuri/expressions.py)."""

import logging

import pytest

from sucuri.expressions import ConditionError, UnknownNameError, evaluate_condition
from sucuri.rendering import Environment


def render(tmp_path, source, context=None):
    path = tmp_path / "probe.suc"
    path.write_text(source, encoding="utf-8")
    return Environment().template(str(path), context or {})


class TestConditionSandbox:
    def test_builtins_are_not_reachable(self):
        with pytest.raises(ConditionError):
            evaluate_condition("__import__('os').getcwd()", {})

    def test_function_calls_are_rejected(self):
        with pytest.raises(ConditionError):
            evaluate_condition("open('/etc/passwd')", {})

    def test_attribute_access_is_rejected(self):
        with pytest.raises(ConditionError):
            evaluate_condition("user.__class__", {"user": {}})

    def test_method_call_on_context_value_is_rejected(self):
        with pytest.raises(ConditionError):
            evaluate_condition("name.upper()", {"name": "bob"})

    def test_lambda_is_rejected(self):
        with pytest.raises(ConditionError):
            evaluate_condition("(lambda: 1)()", {})

    def test_comprehension_is_rejected(self):
        with pytest.raises(ConditionError):
            evaluate_condition("[x for x in (1, 2)]", {})

    def test_exponentiation_is_rejected(self):
        """``**`` turns a short condition into an unbounded CPU burn."""
        with pytest.raises(ConditionError):
            evaluate_condition("9 ** 9 ** 9", {})

    def test_malformed_condition_raises_condition_error(self):
        with pytest.raises(ConditionError):
            evaluate_condition("n ===", {})

    def test_unknown_name_raises_condition_error(self):
        with pytest.raises(UnknownNameError):
            evaluate_condition("missing == 1", {})


class TestBrokenConditionsAreReported:
    """A silently dropped block is indistinguishable from a false condition."""

    def test_malformed_condition_is_logged_as_warning(self, tmp_path, caplog):
        source = "div\n    <if n ===>\n    p never\n    <endif>\n"

        with caplog.at_level(logging.WARNING, logger="sucuri"):
            html = render(tmp_path, source, {"n": 1})

        assert "never" not in html
        assert "could not be evaluated" in caplog.text

    def test_unsupported_construct_is_logged_as_warning(self, tmp_path, caplog):
        source = "div\n    <if name.upper()>\n    p never\n    <endif>\n"

        with caplog.at_level(logging.WARNING, logger="sucuri"):
            render(tmp_path, source, {"name": "bob"})

        assert "could not be evaluated" in caplog.text

    def test_missing_variable_is_not_a_warning(self, tmp_path, caplog):
        """Optional context variables are normal usage, not an authoring mistake."""
        source = "div\n    <if missing == 1>\n    p never\n    <endif>\n"

        with caplog.at_level(logging.WARNING, logger="sucuri"):
            html = render(tmp_path, source, {})

        assert "never" not in html
        assert caplog.text == ""


class TestSideEffectsAreBlocked:
    def test_template_cannot_write_to_disk(self, tmp_path):
        """The strongest proof: a payload that would create a file must not create it."""
        marker = tmp_path / "pwned.txt"
        payload = f"<if __import__('pathlib').Path({str(marker)!r}).write_text('x')>"
        source = f"div\n    {payload}\n    p executed\n    <endif>\n"

        html = render(tmp_path, source)

        assert not marker.exists()
        assert "executed" not in html

    def test_dangerous_condition_renders_nothing_instead_of_crashing(self, tmp_path):
        source = "div\n    <if open('/etc/passwd')>\n    p leaked\n    <endif>\n"

        html = render(tmp_path, source)

        assert "leaked" not in html
        assert "<div>" in html


class TestSupportedConditionsStillWork:
    @pytest.mark.parametrize(
        "expression, context, expected",
        [
            ("n > 5", {"n": 10}, True),
            ("n <= 5", {"n": 10}, False),
            ('role == "admin"', {"role": "admin"}, True),
            ("active == True", {"active": True}, True),
            ('user["score"] >= 100', {"user": {"score": 150}}, True),
            ("data == None", {"data": None}, True),
            ("a and b", {"a": True, "b": False}, False),
            ("a or b", {"a": False, "b": True}, True),
            ("not a", {"a": False}, True),
            ("n + 1 == 3", {"n": 2}, True),
            ('role in ["admin", "editor"]', {"role": "editor"}, True),
            ('role not in ["admin"]', {"role": "editor"}, True),
            ("1 < n < 10", {"n": 5}, True),
            ("1 < n < 3", {"n": 5}, False),
        ],
    )
    def test_expression(self, expression, context, expected):
        assert evaluate_condition(expression, context) is expected

    def test_boolop_short_circuits_before_unknown_name(self):
        assert evaluate_condition("a and missing", {"a": False}) is False
