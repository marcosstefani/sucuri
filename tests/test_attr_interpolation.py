import os
import pytest
from sucuri.rendering import template

BASE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def get_file(name):
    return os.path.join(BASE_DIR, name)


def render(context):
    return template(get_file("test_attr_interpolation.suc"), context)


BASE_CONTEXT = {
    "url": "/home",
    "item": {"url": "/page"},
    "cls": "nav-link",
    "arr": ["A", "B"],
    "connections": [
        {"name": "Alice", "status": "active", "id": "1"},
        {"name": "Bob", "status": "inactive", "id": "2"},
    ],
    "xss": "<script>alert(1)</script>",
}


def test_context_var_in_attribute():
    """Simple {var} is interpolated inside an attribute value."""
    html = render(BASE_CONTEXT)
    assert 'href="/home"' in html


def test_nested_context_var_in_attribute():
    """{obj.prop} nested variable is interpolated inside an attribute value."""
    html = render(BASE_CONTEXT)
    assert 'href="/page"' in html


def test_multiple_interpolated_attributes():
    """Multiple attributes on the same tag are each interpolated."""
    html = render(BASE_CONTEXT)
    assert 'href="/home" class="nav-link"' in html


def test_loop_var_in_attribute_simple_scalar():
    """#loop_var is interpolated in attributes when iterating over a scalar list."""
    html = render(BASE_CONTEXT)
    assert 'class="item-A"' in html
    assert 'class="item-B"' in html


def test_loop_object_property_in_class_attribute():
    """#obj.prop is interpolated in the class attribute when iterating over a list of dicts."""
    html = render(BASE_CONTEXT)
    assert 'class="is-active"' in html
    assert 'class="is-inactive"' in html


def test_loop_object_property_in_data_attribute():
    """#obj.prop is interpolated in a data-* attribute when iterating over a list of dicts."""
    html = render(BASE_CONTEXT)
    assert 'data-id="1"' in html
    assert 'data-id="2"' in html


def test_loop_object_class_and_data_attribute_together():
    """Both class and data attributes are interpolated correctly on the same tag."""
    html = render(BASE_CONTEXT)
    assert 'class="is-active" data-id="1"' in html
    assert 'class="is-inactive" data-id="2"' in html


def test_mixed_static_and_loop_var_in_class():
    """A class value mixing a static prefix and a #loop_var suffix is interpolated."""
    html = render(BASE_CONTEXT)
    assert 'class="dc-tree-item is-active"' in html
    assert 'class="dc-tree-item is-inactive"' in html


def test_xss_escaped_in_attribute_value():
    """A {var} containing HTML special characters is escaped inside attribute values."""
    html = render(BASE_CONTEXT)
    assert 'data-msg="&lt;script&gt;alert(1)&lt;/script&gt;"' in html
    assert 'data-msg="<script>' not in html


def test_missing_var_preserved_in_attribute():
    """An undefined {var} in an attribute value is kept as a literal {var} string."""
    html = render(BASE_CONTEXT)
    assert 'data-x="{missing}"' in html


def test_context_var_in_attribute_reflects_value():
    """Changing the context variable changes the interpolated attribute value."""
    html = render({**BASE_CONTEXT, "url": "/dashboard"})
    assert 'href="/dashboard"' in html
    assert 'href="/home"' not in html


def test_loop_generates_one_element_per_item():
    """Each item in the loop produces a separate element with the correct interpolated attribute."""
    html = render({**BASE_CONTEXT, "arr": ["X", "Y", "Z"]})
    assert 'class="item-X"' in html
    assert 'class="item-Y"' in html
    assert 'class="item-Z"' in html
    assert 'class="item-A"' not in html
