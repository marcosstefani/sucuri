import sys
sys.path.append('...')

from sucuri.element.tag import Tag

def test_should_reflect_when_just_passing_the_tag():
    tag = Tag ('br')
    assert tag.html() == '<br>'

def test_should_reflect_when_just_passing_the_tag_and_value():
    tag = Tag('h1', 'Some text')
    assert tag.html() == '<h1>Some text</h1>'

def test_should_reflect_when_passing_the_tag_and_value_and_properties():
    tag = Tag('h1', 'Some text', 'class="big-label"')
    assert tag.html() == '<h1 class="big-label">Some text</h1>'

def test_should_reflect_when_just_passing_the_tag_and_properties():
    tag = Tag('a', properties='href="#"')
    assert tag.html() == '<a href="#" />'
