import sys
sys.path.append('...')

from sucuri.element.text import Text

def test_should_reflect_when_there_are_variables_one_line():
    text = Text('Hello {a}', {"a": "World!"})
    assert text.render() == 'Hello World!'

def test_should_reflect_when_there_are_variables_more_than_one_line():
    old = """Hello!
    | Text
    | with
    | variable {foo} and
    | more than
    | one line
    """

    new = """Hello!
Text
with
variable foo and
more than
one line"""
    text = Text(old, {"foo": "foo"})
    assert text.render() == new