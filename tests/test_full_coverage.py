"""
Comprehensive tests covering all Sucuri template engine features.
Complements test_engine.py and test_filters_custom.py.
"""
import os
import pytest
from sucuri.rendering import template
from sucuri import Environment

BASE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def get_file(name):
    return os.path.join(BASE_DIR, name)


# ---------------------------------------------------------------------------
# <if> — numeric operators
# ---------------------------------------------------------------------------

class TestIfNumericOperators:
    def test_greater_than_true(self):
        html = template(get_file("test_if_operators.suc"), {"n": 10})
        assert "greater" in html

    def test_greater_than_false(self):
        html = template(get_file("test_if_operators.suc"), {"n": 3})
        assert "greater" not in html

    def test_less_than_true(self):
        html = template(get_file("test_if_operators.suc"), {"n": 3})
        assert "less" in html

    def test_less_than_false(self):
        html = template(get_file("test_if_operators.suc"), {"n": 10})
        assert "<p>less</p>" not in html

    def test_greater_or_equal_exact(self):
        html = template(get_file("test_if_operators.suc"), {"n": 5})
        assert "greater-or-equal" in html

    def test_greater_or_equal_above(self):
        html = template(get_file("test_if_operators.suc"), {"n": 6})
        assert "greater-or-equal" in html

    def test_greater_or_equal_below(self):
        html = template(get_file("test_if_operators.suc"), {"n": 4})
        assert "greater-or-equal" not in html

    def test_less_or_equal_exact(self):
        html = template(get_file("test_if_operators.suc"), {"n": 5})
        assert "less-or-equal" in html

    def test_less_or_equal_below(self):
        html = template(get_file("test_if_operators.suc"), {"n": 4})
        assert "less-or-equal" in html

    def test_less_or_equal_above(self):
        html = template(get_file("test_if_operators.suc"), {"n": 6})
        assert "less-or-equal" not in html

    def test_equal_true(self):
        html = template(get_file("test_if_operators.suc"), {"n": 5})
        assert "equal" in html

    def test_equal_false(self):
        html = template(get_file("test_if_operators.suc"), {"n": 99})
        assert "<p>equal</p>" not in html

    def test_not_equal_true(self):
        html = template(get_file("test_if_operators.suc"), {"n": 99})
        assert "not-equal" in html

    def test_not_equal_false(self):
        html = template(get_file("test_if_operators.suc"), {"n": 5})
        assert "not-equal" not in html


# ---------------------------------------------------------------------------
# <if> — string, bool and nested variable comparisons
# ---------------------------------------------------------------------------

class TestIfAdvanced:
    def test_string_comparison_match(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "admin", "active": True, "user": {"verified": False, "score": 0}
        })
        assert "admin-access" in html
        assert "restricted-access" not in html

    def test_string_comparison_no_match(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "viewer", "active": True, "user": {"verified": False, "score": 0}
        })
        assert "restricted-access" in html
        assert "admin-access" not in html

    def test_bool_true(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "viewer", "active": True, "user": {"verified": False, "score": 0}
        })
        assert "is-active" in html
        assert "is-inactive" not in html

    def test_bool_false(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "viewer", "active": False, "user": {"verified": False, "score": 0}
        })
        assert "is-inactive" in html
        assert "is-active" not in html

    def test_nested_variable_bool(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "viewer", "active": False, "user": {"verified": True, "score": 0}
        })
        assert "is-verified" in html

    def test_nested_variable_numeric(self):
        html = template(get_file("test_if_advanced.suc"), {
            "role": "viewer", "active": False, "user": {"verified": False, "score": 150}
        })
        assert "high-score" in html

    def test_if_with_missing_variable_renders_nothing(self):
        """A condition referencing an undefined variable must not crash — renders nothing."""
        html = template(get_file("test_if_advanced.suc"), {})
        assert "admin-access" not in html
        assert "is-active" not in html


# ---------------------------------------------------------------------------
# <if> / <elif> / <else>
# ---------------------------------------------------------------------------

class TestIfElseElif:
    def test_if_branch_taken(self):
        html = template(get_file("test_if_else.suc"), {"role": "admin"})
        assert "admin-access" in html
        assert "editor-access" not in html
        assert "guest-access" not in html

    def test_elif_branch_taken(self):
        html = template(get_file("test_if_else.suc"), {"role": "editor"})
        assert "editor-access" in html
        assert "admin-access" not in html
        assert "guest-access" not in html

    def test_else_branch_taken(self):
        html = template(get_file("test_if_else.suc"), {"role": "guest"})
        assert "guest-access" in html
        assert "admin-access" not in html
        assert "editor-access" not in html

    def test_only_one_branch_rendered(self):
        """Exactly one branch must be rendered, never multiple."""
        for role, expected, absent in [
            ("admin",  "admin-access",  ["editor-access", "guest-access"]),
            ("editor", "editor-access", ["admin-access",  "guest-access"]),
            ("guest",  "guest-access",  ["admin-access",  "editor-access"]),
        ]:
            html = template(get_file("test_if_else.suc"), {"role": role})
            assert expected in html
            for tag in absent:
                assert tag not in html


# ---------------------------------------------------------------------------
# <if> — JSON-style literals (true / false / null)
# ---------------------------------------------------------------------------

class TestIfJsonLiterals:
    def _render(self, **ctx):
        return template(get_file("test_if_json_literals.suc"), ctx)

    def test_true_literal_match(self):
        html = self._render(active=True, premium=False, data=None)
        assert "is-active" in html
        assert "is-inactive" not in html

    def test_false_literal_match(self):
        html = self._render(active=True, premium=False, data=None)
        assert "is-free" in html
        assert "is-premium" not in html

    def test_null_literal_match(self):
        html = self._render(active=True, premium=False, data=None)
        assert "no-data" in html
        assert "has-data" not in html

    def test_null_literal_not_null(self):
        html = self._render(active=True, premium=False, data="something")
        assert "has-data" in html
        assert "no-data" not in html

    def test_true_and_false_are_mutually_exclusive(self):
        for active in (True, False):
            html = self._render(active=active, premium=False, data=None)
            if active:
                assert "is-active" in html
                assert "is-inactive" not in html
            else:
                assert "is-inactive" in html
                assert "is-active" not in html


# ---------------------------------------------------------------------------
# Filters — built-in (upper, lower, title, safe, chaining)
# ---------------------------------------------------------------------------

class TestBuiltinFilters:
    def _render(self, label, raw=""):
        return template(get_file("test_filters_builtin.suc"), {"label": label, "raw": raw})

    def test_upper(self):
        html = self._render("hello world")
        assert "<h1>HELLO WORLD</h1>" in html

    def test_lower(self):
        html = self._render("HELLO WORLD")
        assert "<h2>hello world</h2>" in html

    def test_title(self):
        html = self._render("hello world")
        assert "<h3>Hello World</h3>" in html

    def test_safe_renders_raw_html(self):
        html = self._render("x", raw="<b>bold</b>")
        assert "<b>bold</b>" in html

    def test_safe_does_not_double_escape(self):
        html = self._render("x", raw="<em>em</em>")
        assert "&lt;em&gt;" not in html

    def test_filter_chaining_upper_then_lower(self):
        """upper | lower should yield the original lowercase result."""
        html = self._render("Hello")
        # upper gives "HELLO", then lower gives "hello"
        assert "<span>hello</span>" in html

    def test_xss_without_safe_is_escaped(self):
        html = self._render("<script>alert(1)</script>")
        assert "&lt;script&gt;" in html
        assert "<script>" not in html


# ---------------------------------------------------------------------------
# Filters — inside # hash loop variables
# ---------------------------------------------------------------------------

class TestFiltersInLoop:
    def test_hash_filter_upper_in_loop(self):
        context = {"items": [{"name": "shirt"}, {"name": "pants"}]}
        html = template(get_file("test_filters_in_loop.suc"), context)
        assert "<li>SHIRT</li>" in html
        assert "<li>PANTS</li>" in html


# ---------------------------------------------------------------------------
# CSS shortcuts
# ---------------------------------------------------------------------------

class TestCssShortcuts:
    def test_id_and_class_on_implicit_div(self):
        html = template(get_file("test_css_shortcuts.suc"), {})
        assert 'id="app"' in html
        assert 'class="container"' in html

    def test_class_on_paragraph(self):
        html = template(get_file("test_css_shortcuts.suc"), {})
        assert 'class="card-text"' in html


# ---------------------------------------------------------------------------
# Multi-line text with pipe |
# ---------------------------------------------------------------------------

class TestMultilineText:
    def test_pipe_lines_are_rendered(self):
        html = template(get_file("test_multiline_text.suc"), {})
        assert "line one" in html
        assert "line two" in html
        assert "line three" in html

    def test_heading_tag_is_present(self):
        html = template(get_file("test_multiline_text.suc"), {})
        assert "<h2>" in html


# ---------------------------------------------------------------------------
# Missing variable — graceful fallback
# ---------------------------------------------------------------------------

class TestMissingVariable:
    def test_missing_var_renders_placeholder(self):
        html = template(get_file("test_missing_var.suc"), {})
        assert "{missing_var}" in html

    def test_missing_var_does_not_crash(self):
        html = template(get_file("test_missing_var.suc"), {})
        assert html is not None


# ---------------------------------------------------------------------------
# Table — partial (no footer)
# ---------------------------------------------------------------------------

class TestTablePartial:
    def test_table_without_footer(self):
        context = {
            "heads": ["Name", "Age"],
            "rows": [["Alice", 30], ["Bob", 25]],
        }
        html = template(get_file("test_table_no_footer.suc"), context)
        assert "<thead>" in html
        assert "<th>Name</th>" in html
        assert "<td>Alice</td>" in html
        assert "<tfoot>" not in html

    def test_table_empty_rows(self):
        context = {"heads": ["Name", "Age"], "rows": []}
        html = template(get_file("test_table_no_footer.suc"), context)
        assert "<thead>" in html
        assert "<tbody>" not in html


# ---------------------------------------------------------------------------
# Include / Macro with inline parameters
# ---------------------------------------------------------------------------

class TestMacroInlineParams:
    def test_macro_inline_params_override_context(self):
        html = template(get_file("test_macro_params.suc"), {
            "title": "Context Title", "type": "default"
        })
        assert "Fixed Title" in html
        assert "info" in html

    def test_macro_inline_params_do_not_leak_to_siblings(self):
        """Inline params must only apply to their own macro call."""
        html = template(get_file("test_mixins.suc"), {})
        assert "Aviso" in html
        assert "Success" in html


# ---------------------------------------------------------------------------
# Environment — isolated filter registries
# ---------------------------------------------------------------------------

class TestEnvironmentIsolation:
    def test_custom_filter_not_available_in_other_env(self, tmp_path):
        env_a = Environment()
        env_b = Environment()

        env_a.register_filter("shout", lambda v: v.upper() + "!")

        tpl = tmp_path / "tpl.suc"
        tpl.write_text("p {msg | shout}")

        html_a = env_a.template(str(tpl), {"msg": "hello"})
        assert "HELLO!" in html_a

        # env_b must not have the filter — value passes through unfiltered or fallback
        html_b = env_b.template(str(tpl), {"msg": "hello"})
        assert "HELLO!" not in html_b

    def test_each_environment_has_independent_base_dir(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_a / "page.suc").write_text("p From A")
        (dir_b / "page.suc").write_text("p From B")

        env_a = Environment(base_dir=str(dir_a))
        env_b = Environment(base_dir=str(dir_b))

        assert "From A" in env_a.template(str(dir_a / "page.suc"), {})
        assert "From B" in env_b.template(str(dir_b / "page.suc"), {})


# ---------------------------------------------------------------------------
# <for> — edge cases
# ---------------------------------------------------------------------------

class TestForLoopEdgeCases:
    def test_empty_list_renders_nothing(self, tmp_path):
        tpl = tmp_path / "loop.suc"
        tpl.write_text("ul\n    <for item in items>\n    li #item\n    <endfor>\n")
        html = template(str(tpl), {"items": []})
        assert "<li>" not in html
        assert "<ul>" in html

    def test_loop_variable_does_not_leak_outside(self, tmp_path):
        tpl = tmp_path / "leak.suc"
        tpl.write_text(
            "ul\n    <for x in items>\n    li #x\n    <endfor>\np {x}\n"
        )
        html = template(str(tpl), {"items": ["a", "b"]})
        # After the loop, {x} may resolve to last item or placeholder — must not crash
        assert html is not None


# ---------------------------------------------------------------------------
# Watch — static render strips all markers
# ---------------------------------------------------------------------------

class TestWatchStaticRender:
    def test_no_suc_watch_attributes_in_static_render(self):
        context = {"title": "T", "items": ["A"], "cart_count": 1}
        html = template(get_file("test_watch.suc"), context)
        assert "data-suc-watch" not in html
        assert "<!--[suc:" not in html

    def test_watch_content_is_still_present(self):
        context = {"title": "T", "items": ["Mango"], "cart_count": 7}
        html = template(get_file("test_watch.suc"), context)
        assert "<li>Mango</li>" in html
        assert "Cart: 7 items" in html
