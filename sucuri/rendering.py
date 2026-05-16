from sucuri.parser import parse_sucuri
from sucuri.compiler import SucuriCompiler
import os

# Global cache of templates already read and built in memory
# Key: 'filepath.suc' + stringification of context (if caching the full text is needed)
# However, the abstract syntax tree (AST) can be cached independently of the context!
_AST_CACHE = {}

def template(filepath, context=None):
    """
    Main function of the Sucuri engine, as described in the original README.
    Reads the file, parses it into an AST (cached in memory for performance),
    and then evaluates the AST using the data injected via `context` to return 
    a string with the final compiled HTML at runtime.
    """
    if context is None:
        context = {}

    # Caching is done in the static parser phase to speed things up significantly
    if filepath not in _AST_CACHE:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template file '{filepath}' not found.")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            sucuri_text = f.read()
        
        # Generate the AST for the entire text
        ast = parse_sucuri(sucuri_text)
        _AST_CACHE[filepath] = ast
        
    tree = _AST_CACHE[filepath]
    
    base_dir = os.path.dirname(filepath) if filepath else "."
    compiler = SucuriCompiler(context, base_dir=base_dir)
    html_output = compiler.compile(tree)
    
    return html_output
