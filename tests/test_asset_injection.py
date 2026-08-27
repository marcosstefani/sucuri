"""Collected <style>/<script> blocks must be injected exactly once, at the end."""

import pytest

from sucuri.rendering import Environment


@pytest.fixture
def templates(tmp_path):
    (tmp_path / "theme.css").write_text("body{color:red}", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    return tmp_path


def render(templates, source, context=None):
    path = templates / "page.suc"
    path.write_text(source, encoding="utf-8")
    return Environment().template(str(path), context or {})


class TestAssetInjection:
    def test_style_is_injected_once(self, templates):
        html = render(templates, "html\n    body\n        css theme\n")

        assert html.count("body{color:red}") == 1

    def test_script_is_injected_once(self, templates):
        html = render(templates, "html\n    body\n        js app\n")

        assert html.count("console.log(1)") == 1

    def test_assets_land_before_the_closing_body(self, templates):
        html = render(templates, "html\n    body\n        css theme\n")

        assert html.index("body{color:red}") < html.rindex("</body>")

    def test_body_in_rendered_content_does_not_duplicate_assets(self, templates):
        """Raw content can contain </body>; only the document's own tag is the anchor."""
        source = "html\n    body\n        css theme\n        p {content | safe}\n"

        html = render(templates, source, {"content": "</body>"})

        assert html.count("body{color:red}") == 1

    def test_assets_are_appended_when_there_is_no_body_tag(self, templates):
        html = render(templates, "div\n    css theme\n")

        assert html.count("body{color:red}") == 1
        assert html.rstrip().endswith("</style>")
