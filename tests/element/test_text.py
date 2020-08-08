import sys
sys.path.append('...')

from sucuri.element.text import Text

def test_should_reflect_when_houver_variaveis_one_line():
    text = Text('Hello {a}', {"a": "World!"})
    assert text.render() == 'Hello World!'