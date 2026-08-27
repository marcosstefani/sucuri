"""Dotted variable lookups, including list indexing."""


from sucuri.rendering import Environment


def render(tmp_path, source, context=None):
    path = tmp_path / "page.suc"
    path.write_text(source, encoding="utf-8")
    return Environment().template(str(path), context or {})


class TestListIndexing:
    def test_index_into_a_list(self, tmp_path):
        html = render(tmp_path, "div\n    p {items.0}\n", {"items": ["first", "second"]})

        assert "first" in html

    def test_index_into_a_list_of_dicts(self, tmp_path):
        context = {"users": [{"name": "Ana"}, {"name": "Bruno"}]}

        html = render(tmp_path, "div\n    p {users.1.name}\n", context)

        assert "Bruno" in html

    def test_out_of_range_index_falls_back_to_placeholder(self, tmp_path):
        html = render(tmp_path, "div\n    p {items.9}\n", {"items": ["only"]})

        assert "only" not in html

    def test_non_numeric_key_on_a_list_falls_back(self, tmp_path):
        html = render(tmp_path, "div\n    p {items.name}\n", {"items": ["only"]})

        assert "only" not in html

    def test_list_values_are_escaped(self, tmp_path):
        html = render(tmp_path, "div\n    p {items.0}\n", {"items": ["<script>"]})

        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestDictLookupStillWorks:
    def test_nested_dict(self, tmp_path):
        context = {"user": {"profile": {"name": "Ana"}}}

        html = render(tmp_path, "div\n    p {user.profile.name}\n", context)

        assert "Ana" in html

    def test_missing_key_falls_back(self, tmp_path):
        html = render(tmp_path, "div\n    p {user.missing}\n", {"user": {}})

        assert "Ana" not in html
