from sucuri.parser import parse_sucuri
from sucuri.compiler import SucuriCompiler
import os

# Global cache of templates already read and built in memory
# Key: 'filepath.suc' + stringification of context (if caching the full text is needed)
# However, the abstract syntax tree (AST) can be cached independently of the context!
_AST_CACHE = {}

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

        if filepath not in _AST_CACHE:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Template file '{filepath}' not found.")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                sucuri_text = f.read()
            
            try:
                ast = parse_sucuri(sucuri_text)
                _AST_CACHE[filepath] = ast
            except Exception as err:
                raise err
            
        tree = _AST_CACHE[filepath]
        
        base_dir = os.path.dirname(filepath) if filepath else self.base_dir
        compiler = SucuriCompiler(context, base_dir=base_dir, filters=self.filters, watch_enabled=self.watch_enabled)
        return compiler.compile(tree)

default_env = Environment()

def template(filepath, context=None):
    """
    Main function of the Sucuri engine, compatible with backward definitions.
    """
    return default_env.template(filepath, context)
