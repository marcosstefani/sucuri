"""Templates must not read files outside their own directory."""

import pytest

from sucuri.rendering import Environment


@pytest.fixture
def secret(tmp_path):
    """A file that sits outside the template directory and must stay unreachable."""
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("TOP-SECRET-VALUE", encoding="utf-8")
    return secret_file


@pytest.fixture
def templates(tmp_path):
    directory = tmp_path / "templates"
    directory.mkdir()
    return directory


def render(templates, source):
    path = templates / "page.suc"
    path.write_text(source, encoding="utf-8")
    return Environment().template(str(path), {})


class TestStyleTraversal:
    def test_style_cannot_escape_template_dir(self, templates, secret):
        secret.rename(secret.with_suffix(".css"))

        html = render(templates, "html\n    body\n        css ../secret\n")

        assert "TOP-SECRET-VALUE" not in html

    def test_style_inside_template_dir_still_loads(self, templates):
        (templates / "theme.css").write_text("body{color:red}", encoding="utf-8")

        html = render(templates, "html\n    body\n        css theme\n")

        assert "body{color:red}" in html


class TestScriptTraversal:
    def test_script_cannot_escape_template_dir(self, templates, secret):
        secret.rename(secret.with_suffix(".js"))

        html = render(templates, "html\n    body\n        js ../secret\n")

        assert "TOP-SECRET-VALUE" not in html

    def test_script_inside_template_dir_still_loads(self, templates):
        (templates / "app.js").write_text("console.log(1)", encoding="utf-8")

        html = render(templates, "html\n    body\n        js app\n")

        assert "console.log(1)" in html


class TestIncludeTraversal:
    def test_include_cannot_escape_template_dir(self, templates, tmp_path):
        outside = tmp_path / "outside.suc"
        outside.write_text("p LEAKED\n", encoding="utf-8")

        html = render(templates, "div\n    include ../outside\n    +outside\n")

        assert "LEAKED" not in html

    def test_include_inside_template_dir_still_loads(self, templates):
        (templates / "card.suc").write_text("p INCLUDED\n", encoding="utf-8")

        html = render(templates, "div\n    include card\n    +card\n")

        assert "INCLUDED" in html


class TestExtendsTraversal:
    def test_extends_cannot_escape_template_dir(self, templates, tmp_path):
        outside = tmp_path / "parent.suc"
        outside.write_text("html\n    body\n        p LEAKED\n", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            render(templates, "extends ../parent\n")

    def test_extends_inside_template_dir_still_loads(self, templates):
        (templates / "layout.suc").write_text(
            "html\n    body\n        p FROM-LAYOUT\n", encoding="utf-8"
        )

        html = render(templates, "extends layout\n")

        assert "FROM-LAYOUT" in html
