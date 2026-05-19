from lark import Lark
from lark.indenter import Indenter

grammar = r"""
?start: block

block: statement*

?statement: stmt _NL
          | block_stmt

block_stmt: if_stmt
          | for_stmt
          | tag_stmt
          | define_block_stmt

stmt: include_stmt
    | style_stmt
    | script_stmt
    | text_inline
    | macro_stmt
    | extends_stmt

extends_stmt: "extends" WS_INLINE PATH
define_block_stmt: "block" WS_INLINE BLOCK_NAME _NL [_INDENT block _DEDENT]

include_stmt: "include" WS_INLINE PATH
style_stmt: "style" WS_INLINE PATH
script_stmt: "script" WS_INLINE PATH
macro_stmt: "+" PATH [macro_attrs] [WS_INLINE TEXT]
macro_attrs: "(" attributes ")"

if_stmt: "<if" WS_INLINE CONDITION ">" _NL block "<endif>" _NL
for_stmt: "<for" WS_INLINE FOR_EXPR ">" _NL block "<endfor>" _NL

tag_stmt: tag_def ["(" attributes ")"] [WS_INLINE TEXT] _NL [_INDENT block _DEDENT]
tag_def: TAG_NAME | CSS_TAG

attributes: attr (WS_INLINE attr)*
attr: ATTR_NAME ["=" ATTR_VALUE]

text_inline: "|" WS_INLINE? TEXT

TAG_NAME: /[a-zA-Z0-9\-]+/
CSS_TAG: /([a-zA-Z0-9\-]+)?(#[a-zA-Z0-9\-]+|\.[a-zA-Z0-9\-]+)+/
BLOCK_NAME: /[a-zA-Z0-9_]+/
ATTR_NAME: /[a-zA-Z0-9\-\._]+/
ATTR_VALUE: /"[^"]*"/ | /'[^']*'/
PATH: /[a-zA-Z0-9\/\.\-_]+/
CONDITION: /[^>]+/
FOR_EXPR: /[^>]+/
TEXT: /[^\n]+/
WS_INLINE: /[ \t]+/

_NL: /(\r?\n[\t ]*)+/

%declare _INDENT _DEDENT
"""

class SucuriIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4

parser = Lark(grammar, parser='lalr', lexer='contextual', postlex=SucuriIndenter())

class SucuriSyntaxError(Exception):
    def __init__(self, message, line, column):
        super().__init__(message)
        self.line = line
        self.column = column

def parse_sucuri(text):
    from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters
    try:
        return parser.parse(text + "\n")
    except UnexpectedToken as e:
        msg = f"Syntax error at line {e.line}, column {e.column}.\nUnexpected token: {e.token}\nExpected: {', '.join(e.expected)}"
        raise SucuriSyntaxError(msg, e.line, e.column) from e
    except UnexpectedCharacters as e:
        msg = f"Syntax error at line {e.line}, column {e.column}.\nUnexpected characters.\nAllowed: {', '.join(e.allowed)}"
        raise SucuriSyntaxError(msg, e.line, e.column) from e
    except UnexpectedInput as e:
        msg = f"Syntax error at line {e.line}, column {e.column}."
        raise SucuriSyntaxError(msg, e.line, e.column) from e
