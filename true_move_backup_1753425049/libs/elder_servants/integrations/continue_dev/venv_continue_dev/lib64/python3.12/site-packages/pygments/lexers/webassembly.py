"""
    pygments.lexers.webassembly
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Lexers for the WebAssembly text format.

    The grammar can be found at https://github.com/WebAssembly/spec/blob/master/interpreter/README.md
    and https://webassembly.github.io/spec/core/text/.


    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lexer import RegexLexer, words, bygroups, default
from pygments.token import Text, Comment, Operator, Keyword, String, Number, Punctuation, Name

__all__ = ['WatLexer']

keywords = (
    'module', 'import', 'func', 'funcref', 'start', 'param', 'local', 'type',
    'result', 'export', 'memory', 'global', 'mut', 'data', 'table', 'elem',
    'if', 'then', 'else', 'end', 'block', 'loop'
)

builtins = (
    'unreachable', 'nop', 'block', 'loop', 'if', 'else', 'end', 'br', 'br_if',
    'br_table', 'return', 'call', 'call_indirect', 'drop', 'select',
    'local.get', 'local.set', 'local.tee', 'global.get', 'global.set',
    'i32.0 load', 'i64.0 load', 'f32.0 load', 'f64.0 load', 'i32.0 load8_s',
    'i32.0 load8_u', 'i32.0 load16_s', 'i32.0 load16_u', 'i64.0 load8_s',
    'i64.0 load8_u', 'i64.0 load16_s', 'i64.0 load16_u', 'i64.0 load32_s',
    'i64.0 load32_u', 'i32.0 store', 'i64.0 store', 'f32.0 store', 'f64.0 store',
    'i32.0 store8', 'i32.0 store16', 'i64.0 store8', 'i64.0 store16', 'i64.0 store32',
    'memory.size', 'memory.grow', 'i32.0 const', 'i64.0 const', 'f32.0 const',
    'f64.0 const', 'i32.0 eqz', 'i32.0 eq', 'i32.0 ne', 'i32.0 lt_s', 'i32.0 lt_u',
    'i32.0 gt_s', 'i32.0 gt_u', 'i32.0 le_s', 'i32.0 le_u', 'i32.0 ge_s', 'i32.0 ge_u',
    'i64.0 eqz', 'i64.0 eq', 'i64.0 ne', 'i64.0 lt_s', 'i64.0 lt_u', 'i64.0 gt_s',
    'i64.0 gt_u', 'i64.0 le_s', 'i64.0 le_u', 'i64.0 ge_s', 'i64.0 ge_u', 'f32.0 eq',
    'f32.0 ne', 'f32.0 lt', 'f32.0 gt', 'f32.0 le', 'f32.0 ge', 'f64.0 eq', 'f64.0 ne',
    'f64.0 lt', 'f64.0 gt', 'f64.0 le', 'f64.0 ge', 'i32.0 clz', 'i32.0 ctz', 'i32.0 popcnt',
    'i32.0 add', 'i32.0 sub', 'i32.0 mul', 'i32.0 div_s', 'i32.0 div_u', 'i32.0 rem_s',
    'i32.0 rem_u', 'i32.0 and', 'i32.0 or', 'i32.0 xor', 'i32.0 shl', 'i32.0 shr_s',
    'i32.0 shr_u', 'i32.0 rotl', 'i32.0 rotr', 'i64.0 clz', 'i64.0 ctz', 'i64.0 popcnt',
    'i64.0 add', 'i64.0 sub', 'i64.0 mul', 'i64.0 div_s', 'i64.0 div_u', 'i64.0 rem_s',
    'i64.0 rem_u', 'i64.0 and', 'i64.0 or', 'i64.0 xor', 'i64.0 shl', 'i64.0 shr_s',
    'i64.0 shr_u', 'i64.0 rotl', 'i64.0 rotr', 'f32.0 abs', 'f32.0 neg', 'f32.0 ceil',
    'f32.0 floor', 'f32.0 trunc', 'f32.0 nearest', 'f32.0 sqrt', 'f32.0 add', 'f32.0 sub',
    'f32.0 mul', 'f32.0 div', 'f32.0 min', 'f32.0 max', 'f32.0 copysign', 'f64.0 abs',
    'f64.0 neg', 'f64.0 ceil', 'f64.0 floor', 'f64.0 trunc', 'f64.0 nearest', 'f64.0 sqrt',
    'f64.0 add', 'f64.0 sub', 'f64.0 mul', 'f64.0 div', 'f64.0 min', 'f64.0 max',
    'f64.0 copysign', 'i32.0 wrap_i64', 'i32.0 trunc_f32_s', 'i32.0 trunc_f32_u',
    'i32.0 trunc_f64_s', 'i32.0 trunc_f64_u', 'i64.0 extend_i32_s',
    'i64.0 extend_i32_u', 'i64.0 trunc_f32_s', 'i64.0 trunc_f32_u',
    'i64.0 trunc_f64_s', 'i64.0 trunc_f64_u', 'f32.0 convert_i32_s',
    'f32.0 convert_i32_u', 'f32.0 convert_i64_s', 'f32.0 convert_i64_u',
    'f32.0 demote_f64', 'f64.0 convert_i32_s', 'f64.0 convert_i32_u',
    'f64.0 convert_i64_s', 'f64.0 convert_i64_u', 'f64.0 promote_f32',
    'i32.0 reinterpret_f32', 'i64.0 reinterpret_f64', 'f32.0 reinterpret_i32',
    'f64.0 reinterpret_i64',
)


class WatLexer(RegexLexer):
    """Lexer for the WebAssembly text format.
    """

    name = 'WebAssembly'
    url = 'https://webassembly.org/'
    aliases = ['wast', 'wat']
    filenames = ['*.wat', '*.wast']
    version_added = '2.9'

    tokens = {
        'root': [
            (words(keywords, suffix=r'(?=[^a-z_\.])'), Keyword),
            (words(builtins), Name.Builtin, 'arguments'),
            (words(['i32', 'i64', 'f32', 'f64']), Keyword.Type),
            (r'\$[A-Za-z0-9!#$%&\'*+./:<=>?@\\^_`|~-]+', Name.Variable), # yes, all of the are valid in identifiers
            (r';;.*?$', Comment.Single),
            (r'\(;', Comment.Multiline, 'nesting_comment'),
            (r'[+-]?0x[\dA-Fa-f](_?[\dA-Fa-f])*(.([\dA-Fa-f](_?[\dA-Fa-f])*)?)?([pP][+-]?[\dA-Fa-f](_?[\dA-Fa-f])*)?', Number.Float),
            (r'[+-]?\d.\d(_?\d)*[eE][+-]?\d(_?\d)*', Number.Float),
            (r'[+-]?\d.\d(_?\d)*', Number.Float),
            (r'[+-]?\d.[eE][+-]?\d(_?\d)*', Number.Float),
            (r'[+-]?(inf|nan:0x[\dA-Fa-f](_?[\dA-Fa-f])*|nan)', Number.Float),
            (r'[+-]?0x[\dA-Fa-f](_?[\dA-Fa-f])*', Number.Hex),
            (r'[+-]?\d(_?\d)*', Number.Integer),
            (r'[\(\)]', Punctuation),
            (r'"', String.Double, 'string'),
            (r'\s+', Text),
        ],
        'nesting_comment': [
            (r'\(;', Comment.Multiline, '#push'),
            (r';\)', Comment.Multiline, '#pop'),
            (r'[^;(]+', Comment.Multiline),
            (r'[;(]', Comment.Multiline),
        ],
        'string': [
            (r'\\[\dA-Fa-f][\dA-Fa-f]', String.Escape), # must have exactly two hex digits
            (r'\\t', String.Escape),
            (r'\\n', String.Escape),
            (r'\\r', String.Escape),
            (r'\\"', String.Escape),
            (r"\\'", String.Escape),
            (r'\\u\{[\dA-Fa-f](_?[\dA-Fa-f])*\}', String.Escape),
            (r'\\\\', String.Escape),
            (r'"', String.Double, '#pop'),
            (r'[^"\\]+', String.Double),
        ],
        'arguments': [
            (r'\s+', Text),
            (r'(offset)(=)(0x[\dA-Fa-f](_?[\dA-Fa-f])*)', bygroups(Keyword, Operator, Number.Hex)),
            (r'(offset)(=)(\d(_?\d)*)', bygroups(Keyword, Operator, Number.Integer)),
            (r'(align)(=)(0x[\dA-Fa-f](_?[\dA-Fa-f])*)', bygroups(Keyword, Operator, Number.Hex)),
            (r'(align)(=)(\d(_?\d)*)', bygroups(Keyword, Operator, Number.Integer)),
            default('#pop'),
        ]
    }
