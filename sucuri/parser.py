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
macro_stmt: "+" PATH ["(" attributes ")"] [WS_INLINE TEXT]? _NL [_INDENT block _DEDENT]

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

def parse_sucuri(text):
    return parser.parse(text + "\n")
