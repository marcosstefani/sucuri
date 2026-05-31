import os
import pytest
from sucuri.parser import parse_sucuri
from sucuri.compiler import SucuriCompiler
from sucuri.rendering import template

BASE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def get_file(name):
    return os.path.join(BASE_DIR, name)

def test_full_rendering_from_file():
    context = {"name": "Bob"}
    html = template(get_file("test_rendering.suc"), context)
    assert "<h1>Hello Bob!" in html
    assert "Welcome to Sucuri template engine." in html
    assert "<a href='#'>Bob</a>" in html  # via include link
    assert "<style>body { background: red; }\n</style>" in html # via style

def test_parser_and_inline_text():
    html = template(get_file("test_inline_text.suc"), {})
    assert '<h1>Title' in html
    assert 'Desc' in html

def test_attributes_parsing():
    html = template(get_file("test_attributes.suc"), {})
    assert '<a href="#" target="_blank">Link</a>' in html
    assert '<input type="checkbox" checked>' in html

def test_if_condition():
    html_true = template(get_file("test_if.suc"), {"n": 1})
    assert "<h1>Is One</h1>" in html_true
    assert "Not One" not in html_true

    html_false = template(get_file("test_if.suc"), {"n": 2})
    assert "<h1>Not One</h1>" in html_false
    assert "Is One" not in html_false

def test_for_loop():
    html = template(get_file("test_for.suc"), {"arr": ["A", "B"]})
    assert "<li>Item A</li>" in html
    assert "<li>Item B</li>" in html

def test_nested_for_loop_and_pound_variable():
    html = template(get_file("test_for_nested.suc"), {"arr": ["Out"], "inner": [1, 2]})
    assert "<li>Value Out</li>" in html
    assert "<li>Nested 1</li>" in html
    assert "<li>Nested 2</li>" in html

def test_for_nested_var():
    html = template(get_file("test_for_nested_var.suc"), {"nested": {"list": [1, 2, 3]}})
    assert "<li>1</li>" in html
    assert "<li>2</li>" in html
    assert "<li>3</li>" in html

def test_list_checkboxes():
    html = template(get_file("test_compiler.suc"), {"name": "Test", "items": [1, 2], "checked": [1]})
    assert 'type="checkbox" id="ck-1" checked="checked"' in html
    assert 'type="checkbox" id="ck-2"' in html
    assert 'type="checkbox" id="ck-2" checked="checked"' not in html

def test_list_checkboxes_custom_variable():
    context = {"my_items": ['one', 'two', 'five'], "my_checked": ['two']}
    html = template(get_file("test_checkboxes_custom.suc"), context)
    assert '<input type="checkbox" id="ck-one">one' in html
    assert '<input type="checkbox" id="ck-two" checked="checked">two' in html
    assert '<input type="checkbox" id="ck-five">five' in html

def test_list_unordered():
    html = template(get_file("test_compiler.suc"), {"name": "Test", "items": [1, 2], "checked": []})
    assert '<ul class="ul-squares">' in html
    assert "<li> 1 </li>" in html
    assert "<li> 2 </li>" in html

def test_script_tag():
    html = template(get_file("test_compiler.suc"), {"name": "Test", "items": [], "checked": []})
    assert "<script>console.log('hi');\n</script>" in html

def test_list_as_variable_nested():
    context = {"var1": [1, 2], "example": {"var2": [3, 4]}}
    # we can use both in template as lists
    html = template(get_file("test_list_variable.suc"), context)
    assert "<li> 1 </li>" in html
    assert "<li> 2 </li>" in html
    assert "<li> 3 </li>" in html
    assert "<li> 4 </li>" in html

def test_table_tag():
    context = {
        "heads": ["A", "B"],
        "rows": [[1, 2], [3, 4]],
        "footers": ["End A", "End B"]
    }
    html = template(get_file("test_table.suc"), context)
    assert '<table class="table" id="tb-one">' in html
    assert "<thead>" in html
    assert "<th>A</th>" in html
    assert "<th>B</th>" in html
    assert "<tbody>" in html
    assert "<td>1</td>" in html
    assert "<td>2</td>" in html
    assert "<td>3</td>" in html
    assert "<td>4</td>" in html
    assert "<tfoot>" in html
    assert "<td>End A</td>" in html
    assert "<td>End B</td>" in html

def test_xss_protection():
    context = {"msg": "<script>alert(1)</script>"}
    html = template(get_file("test_xss.suc"), context)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>" not in html

def test_template_inheritance():
    context = {"title": "My Page"}
    html = template(get_file("test_extends.suc"), context)
    assert "<title>My Page</title>" in html
    assert "Bem-vindo à Home" in html
    assert "Rodape do Index" in html
    assert "div id=\"content\"" in html
    assert "div id=\"footer\"" in html


def test_watch_simple_render_ignores_wrapper():
    """Simple render must output block content without any watch wrapper or markers."""
    context = {"title": "Shop", "items": ["Apple", "Banana"], "cart_count": 3}
    html = template(get_file("test_watch.suc"), context)

    # Content inside watch blocks must be present
    assert "<li>Apple</li>" in html
    assert "<li>Banana</li>" in html
    assert "Cart: 3 items" in html

    # No SSE wrapper elements or comments should be emitted
    assert 'data-suc-watch=' not in html
    assert '<!--[suc:' not in html


def test_watch_compiler_watch_enabled_emits_wrapper():
    """Compiler with watch_enabled=True must emit the wrapper div and markers."""
    from sucuri.parser import parse_sucuri

    with open(get_file("test_watch.suc"), "r", encoding="utf-8") as f:
        source = f.read()

    context = {"title": "Shop", "items": ["Apple", "Banana"], "cart_count": 3}
    tree = parse_sucuri(source)
    compiler = SucuriCompiler(context, base_dir=BASE_DIR, watch_enabled=True)
    html = compiler.compile(tree)

    # Content inside watch blocks must still be present
    assert "<li>Apple</li>" in html
    assert "<li>Banana</li>" in html
    assert "Cart: 3 items" in html

    # Wrapper elements and markers must be present
    assert 'data-suc-watch="products"' in html
    assert 'data-suc-watch="cart"' in html
    assert '<!--[suc:products:start]-->' in html
    assert '<!--[suc:products:end]-->' in html
    assert '<!--[suc:cart:start]-->' in html
    assert '<!--[suc:cart:end]-->' in html


def test_watch_multiple_blocks_render_independently():
    """Each watch block's content is rendered correctly in simple mode."""
    context = {"title": "T", "items": ["X"], "cart_count": 0}
    html = template(get_file("test_watch.suc"), context)

    assert "<li>X</li>" in html
    assert "Cart: 0 items" in html
    assert 'data-suc-watch=' not in html


def test_code_block_multiline_preserves_whitespace_and_blank_lines():
    html = template(get_file("test_code_multiline.suc"), {})

    expected = "class User:\n    def save(self):\n\n        pass"
    assert expected in html


def test_code_block_single_line_keeps_previous_behavior():
    html = template(get_file("test_code_single_line.suc"), {})
    assert "<code>print(\"ok\")</code>" in html


def test_non_code_pipe_whitespace_behavior_is_unchanged():
    html = template(get_file("test_non_code_pipe_whitespace.suc"), {})
    assert "<p>" in html
    assert "keep current behavior" in html
    assert "\n       keep current behavior" not in html


