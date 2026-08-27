"""SucuriApp.render must not reach templates outside its template_dir."""

import pytest

from sucuri.paths import resolve_within
from sucuri.server import SucuriApp


@pytest.fixture
def app(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "index.suc").write_text("div\n    p HOME\n", encoding="utf-8")
    return SucuriApp(template_dir=str(templates))


class TestRenderConfinement:
    def test_template_inside_the_directory_renders(self, app):
        assert "HOME" in app.render("index.suc", {})

    def test_traversal_is_refused(self, app, tmp_path):
        (tmp_path / "outside.suc").write_text("div\n    p LEAKED\n", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            app.render("../outside.suc", {})

    def test_absolute_path_is_refused(self, app, tmp_path):
        outside = tmp_path / "outside.suc"
        outside.write_text("div\n    p LEAKED\n", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            app.render(str(outside), {})


class TestResolveWithin:
    def test_plain_name_resolves(self, tmp_path):
        assert resolve_within(str(tmp_path), "a.suc") is not None

    def test_parent_traversal_is_refused(self, tmp_path):
        assert resolve_within(str(tmp_path), "../a.suc") is None

    def test_nested_traversal_that_returns_inside_is_allowed(self, tmp_path):
        (tmp_path / "sub").mkdir()

        assert resolve_within(str(tmp_path), "sub/../a.suc") is not None

    def test_symlink_pointing_outside_is_refused(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        base = tmp_path / "base"
        base.mkdir()
        (base / "link").symlink_to(outside)

        assert resolve_within(str(base), "link/secret.txt") is None

    def test_extension_is_appended_when_missing(self, tmp_path):
        resolved = resolve_within(str(tmp_path), "page", ".suc")

        assert resolved.endswith("page.suc")

    def test_empty_path_is_refused(self, tmp_path):
        assert resolve_within(str(tmp_path), "") is None
