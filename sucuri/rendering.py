from sucuri.parser import parse_sucuri
from sucuri.compiler import SucuriCompiler
from collections import OrderedDict
import os

# Default number of parsed templates kept in memory.
_DEFAULT_CACHE_SIZE = 128


class _TemplateCache:
    """Bounded, mtime-aware cache of parsed template ASTs.

    A parsed tree depends only on file content, so entries are shared across
    Environments. They are keyed by real path and revalidated against the file's
    mtime, which means a template edited on disk is re-parsed without any external
    invalidation hook. Capacity is bounded so a long-running process cannot grow
    without limit when template paths are generated dynamically.
    """

    def __init__(self, maxsize=_DEFAULT_CACHE_SIZE):
        self.maxsize = maxsize
        self._entries = OrderedDict()

    @staticmethod
    def _key(filepath):
        return os.path.realpath(filepath)

    def get(self, filepath, mtime):
        key = self._key(filepath)
        entry = self._entries.get(key)
        if entry is None:
            return None
        cached_mtime, tree = entry
        if cached_mtime != mtime:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return tree

    def set(self, filepath, mtime, tree):
        key = self._key(filepath)
        self._entries[key] = (mtime, tree)
        self._entries.move_to_end(key)
        while len(self._entries) > self.maxsize:
            self._entries.popitem(last=False)

    def clear(self):
        self._entries.clear()

    def __contains__(self, filepath):
        return self._key(filepath) in self._entries

    def __getitem__(self, filepath):
        return self._entries[self._key(filepath)][1]

    def __delitem__(self, filepath):
        del self._entries[self._key(filepath)]

    def __len__(self):
        return len(self._entries)


_AST_CACHE = _TemplateCache()

class Environment:
    """
    Represents a templating environment that can hold custom plugins, filters,
    and configurations.
    """
    def __init__(self, base_dir=".", watch_enabled=False):
        self.base_dir = base_dir
        self.filters = {}
        self.watch_enabled = watch_enabled

    def register_filter(self, name, filter_func=None):
        if filter_func is None:
            def decorator(f):
                self.filters[name] = f
                return f
            return decorator
        self.filters[name] = filter_func
        return filter_func

    def template(self, filepath, context=None):
        if context is None:
            context = {}

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template file '{filepath}' not found.")

        mtime = os.path.getmtime(filepath)
        tree = _AST_CACHE.get(filepath, mtime)
        if tree is None:
            with open(filepath, 'r', encoding='utf-8') as f:
                sucuri_text = f.read()
            tree = parse_sucuri(sucuri_text)
            _AST_CACHE.set(filepath, mtime, tree)

        base_dir = os.path.dirname(filepath) if filepath else self.base_dir
        compiler = SucuriCompiler(context, base_dir=base_dir, filters=self.filters, watch_enabled=self.watch_enabled)
        return compiler.compile(tree)

default_env = Environment()

def template(filepath, context=None):
    """
    Main function of the Sucuri engine, compatible with backward definitions.
    """
    return default_env.template(filepath, context)
