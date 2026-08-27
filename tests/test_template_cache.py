"""The parsed-AST cache must stay bounded and never serve a stale template."""

import os
import time

from sucuri.rendering import _AST_CACHE, _TemplateCache, Environment


def write(path, source):
    """Write a template, ensuring mtime differs from any previous write."""
    path.write_text(source, encoding="utf-8")
    # Coarse filesystem mtime resolution would otherwise hide the change.
    os.utime(path, (time.time() + 1, time.time() + 1))


class TestInvalidation:
    def test_edited_template_is_reparsed(self, tmp_path):
        path = tmp_path / "page.suc"
        write(path, "div\n    p BEFORE\n")
        env = Environment()

        assert "BEFORE" in env.template(str(path), {})

        write(path, "div\n    p AFTER\n")

        assert "AFTER" in env.template(str(path), {})

    def test_unchanged_template_reuses_parsed_tree(self, tmp_path):
        path = tmp_path / "page.suc"
        write(path, "div\n    p HELLO\n")
        env = Environment()

        env.template(str(path), {})
        cached = _AST_CACHE[str(path)]
        env.template(str(path), {})

        assert _AST_CACHE[str(path)] is cached

    def test_equivalent_paths_share_one_entry(self, tmp_path):
        path = tmp_path / "page.suc"
        write(path, "div\n    p HELLO\n")
        _AST_CACHE.clear()
        env = Environment()

        env.template(str(path), {})
        env.template(str(tmp_path / "." / "page.suc"), {})

        assert len(_AST_CACHE) == 1


class TestBounding:
    def test_cache_does_not_grow_past_maxsize(self, tmp_path):
        cache = _TemplateCache(maxsize=3)

        for index in range(10):
            cache.set(tmp_path / f"t{index}.suc", index, f"tree-{index}")

        assert len(cache) == 3

    def test_least_recently_used_entry_is_evicted_first(self, tmp_path):
        cache = _TemplateCache(maxsize=2)
        first, second, third = (tmp_path / f"t{i}.suc" for i in range(3))

        cache.set(first, 1, "a")
        cache.set(second, 1, "b")
        cache.get(first, 1)  # first becomes most recently used
        cache.set(third, 1, "c")

        assert first in cache
        assert third in cache
        assert second not in cache

    def test_stale_entry_is_dropped_on_read(self, tmp_path):
        cache = _TemplateCache()
        path = tmp_path / "t.suc"
        cache.set(path, 1, "old")

        assert cache.get(path, 2) is None
        assert path not in cache


class TestMissingTemplate:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        env = Environment()

        try:
            env.template(str(tmp_path / "nope.suc"), {})
        except FileNotFoundError as error:
            assert "not found" in str(error)
        else:
            raise AssertionError("expected FileNotFoundError")
