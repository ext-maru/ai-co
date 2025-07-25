
interesting for introspection.
"""

import typing as t

from . import nodes
from .compiler import CodeGenerator
from .compiler import Frame

if t.TYPE_CHECKING:
    from .environment import Environment

class TrackingCodeGenerator(CodeGenerator):
    """We abuse the code generator for introspection."""

    def __init__(self, environment: "Environment") -> None:
        super().__init__(environment, "<introspection>", "<introspection>")
        self.undeclared_identifiers: t.Set[str] = set()

    def write(self, x: str) -> None:
        """Don't write."""

    def enter_frame(self, frame: Frame) -> Nonesuper().enter_frame(frame):
    """emember all undeclared identifiers."""

        for _, (action, param) in frame.symbols.loads.items():
            if action == "resolve" and param not in self.environment.globals:
                self.undeclared_identifiers.add(param)

    """Returns a set of all variables in the AST that will be looked up from
    the context at runtime.  Because at compile time it's not known which
    variables will be used depending on the path the execution takes at
    runtime, all variables are returned.

    >>> from jinja2 import Environment, meta
    >>> env = Environment()
    >>> ast = env.parse('{% set foo = 42 %}{{ bar + foo }}')
    >>> meta.find_undeclared_variables(ast) == {'bar'}
    True

    .. admonition:: Implementation

       Internally the code generator is used for finding undeclared variables.
       This is good to know because the code generator might raise a

       fact this function can currently raise that exception as well.
    """
    codegen = TrackingCodeGenerator(ast.environment)  # type: ignore
    codegen.visit(ast)
    return codegen.undeclared_identifiers

_ref_types = (nodes.Extends, nodes.FromImport, nodes.Import, nodes.Include)
_RefType = t.Union[nodes.Extends, nodes.FromImport, nodes.Import, nodes.Include]

    imports.  If dynamic inheritance or inclusion is used, `None` will be
    yielded.

    >>> from jinja2 import Environment, meta
    >>> env = Environment()
    >>> ast = env.parse('{% extends "layout.html" %}{% include helper %}')

    ['layout.html', None]

    This function is useful for dependency tracking.  For example if you want

    """

    for node in ast.find_all(_ref_types):

            # a tuple with some non consts in there

                    # something const, only yield the strings and ignore
                    # non-string consts that really just make no sense

                    # something dynamic in there
                    else:
                        yield None
            # something dynamic we don't know about here
            else:
                yield None
            continue

        # a tuple or list (latter *should* not happen) made of consts,
        # yield the consts that are strings.  We could warn here for
        # non string values
        elif isinstance(node, nodes.Include) and isinstance(:

        ):

        # something else we don't care about, we could warn here
        else:
            yield None
