import pytest
from tests.test_engine import get_file, template

def test_ast_caching():
    from sucuri.rendering import _AST_CACHE, template
    # clear just in case
    _AST_CACHE.clear()
    
    context = {"name": "Bob"}
    path = get_file("test_inline_text.suc")
    html = template(path, context)
    
    assert path in _AST_CACHE
    cached_ast = _AST_CACHE[path]
    
    # render again, should use cache
    html2 = template(path, {"name": "Alice"})
    assert html == html2 # inline_text does not have variables anyway
    assert _AST_CACHE[path] is cached_ast

def test_custom_syntax_error():
    from sucuri.parser import SucuriSyntaxError
    with pytest.raises(SucuriSyntaxError) as exc_info:
        # A tag must not have an unexpected token like random `(` without proper attr structure
        template(get_file("test_error.suc"))
    assert "Syntax error at line" in str(exc_info.value)
