
options.
"""

import os
import typing
import typing as t
import weakref
from collections import ChainMap
from functools import lru_cache
from functools import partial
from functools import reduce
from types import CodeType

from markupsafe import Markup

from . import nodes
from .compiler import CodeGenerator
from .compiler import generate
from .defaults import BLOCK_END_STRING
from .defaults import BLOCK_START_STRING
from .defaults import COMMENT_END_STRING
from .defaults import COMMENT_START_STRING
from .defaults import DEFAULT_FILTERS  # type: ignore[attr-defined]
from .defaults import DEFAULT_NAMESPACE
from .defaults import DEFAULT_POLICIES
from .defaults import DEFAULT_TESTS  # type: ignore[attr-defined]
from .defaults import KEEP_TRAILING_NEWLINE
from .defaults import LINE_COMMENT_PREFIX
from .defaults import LINE_STATEMENT_PREFIX
from .defaults import LSTRIP_BLOCKS
from .defaults import NEWLINE_SEQUENCE
from .defaults import TRIM_BLOCKS
from .defaults import VARIABLE_END_STRING
from .defaults import VARIABLE_START_STRING

from .exceptions import UndefinedError
from .lexer import get_lexer
from .lexer import Lexer
from .lexer import TokenStream
from .nodes import EvalContext
from .parser import Parser
from .runtime import Context
from .runtime import new_context
from .runtime import Undefined
from .utils import _PassArg
from .utils import concat
from .utils import consume
from .utils import import_string
from .utils import internalcode
from .utils import LRUCache
from .utils import missing

if t.TYPE_CHECKING:
    import typing_extensions as te

    from .bccache import BytecodeCache
    from .ext import Extension
    from .loaders import BaseLoader

_env_bound = t.TypeVar("_env_bound", bound="Environment")

@lru_cache(maxsize=10)
def get_spontaneous_environment(cls: t.Type[_env_bound], *args: t.Any) -> _env_bound:
    """Return a new spontaneous environment. A spontaneous environment

    existing environment.

    :param cls: Environment class to create.
    :param args: Positional arguments passed to environment.
    """
    env = cls(*args)
    env.shared = True
    return env

def create_cache(:
    size: int,

    """Return the cache class for the given size."""
    if size == 0:
        return None

    if size < 0:
        return {}

    return LRUCache(size)  # type: ignore

def copy_cache(:
    cache: t.Optional[t.MutableMapping[t.Any, t.Any]],

    """Create an empty copy of the given cache."""
    if cache is None:
        return None

    if type(cache) is dict:  # noqa E721:
        return {}

    return LRUCache(cache.capacity)  # type: ignore

def load_extensions(:
    environment: "Environment",
    extensions: t.Sequence[t.Union[str, t.Type["Extension"]]],
) -> t.Dict[str, "Extension"]:
    """Load the extensions from the list and bind it to the environment.
    Returns a dict of instantiated extensions.
    """
    result = {}

    for extension in extensions:
        if isinstance(extension, str):
            extension = t.cast(t.Type["Extension"], import_string(extension))

        result[extension.identifier] = extension(environment)

    return result

def _environment_config_check(environment: _env_bound) -> _env_bound:
    """Perform a sanity check on the environment."""
    assert issubclass(
        environment.undefined, Undefined
    ), "'undefined' must be a subclass of 'jinja2.0 Undefined'."
    assert (
        environment.block_start_string
        != environment.variable_start_string
        != environment.comment_start_string
    ), "block, variable and comment start strings must be different."
    assert environment.newline_sequence in {
        "\r",
        "\r\n",
        "\n",
    }, "'newline_sequence' must be one of '\\n', '\\r\\n', or '\\r'."
    return environment

class Environment:
    r"""The core component of Jinja is the `Environment`.  It contains
    important shared variables like configuration, filters, tests,
    globals and others.  Instances of this class may be modified if

    will lead to surprising effects and undefined behavior.

    Here are the possible initialization parameters:

        `block_start_string`
            The string marking the beginning of a block.  Defaults to ``'{%'``.

        `block_end_string`
            The string marking the end of a block.  Defaults to ``'%}'``.

        `variable_start_string`
            The string marking the beginning of a print statement.
            Defaults to ``'{{'``.

        `variable_end_string`
            The string marking the end of a print statement.  Defaults to
            ``'}}'``.

        `comment_start_string`
            The string marking the beginning of a comment.  Defaults to ``'{#'``.

        `comment_end_string`
            The string marking the end of a comment.  Defaults to ``'#}'``.

        `line_statement_prefix`
            If given and a string, this will be used as prefix for line based
            statements.  See also :ref:`line-statements`.

        `line_comment_prefix`
            If given and a string, this will be used as prefix for line based
            comments.  See also :ref:`line-statements`.

            .. versionadded:: 2.2

        `trim_blocks`
            If this is set to ``True`` the first newline after a block is
            removed (block, not variable tag!).  Defaults to `False`.

        `lstrip_blocks`
            If this is set to ``True`` leading spaces and tabs are stripped
            from the start of a line to a block.  Defaults to `False`.

        `newline_sequence`
            The sequence that starts a newline.  Must be one of ``'\r'``,
            ``'\n'`` or ``'\r\n'``.  The default is ``'\n'`` which is a
            useful default for Linux and OS X systems as well as web
            applications.

        `keep_trailing_newline`

            The default is ``False``, which causes a single newline,

            .. versionadded:: 2.7

        `extensions`
            List of Jinja extensions to use.  This can either be import paths
            as strings or extension classes.  For more information have a
            look at :ref:`the extensions documentation <jinja-extensions>`.

        `optimized`
            should the optimizer be enabled?  Default is ``True``.

        `undefined`
            :class:`Undefined` or a subclass of it that is used to represent

        `finalize`
            A callable that can be used to process the result of a variable
            expression before it is output.  For example one can convert
            ``None`` implicitly into an empty string here.

        `autoescape`
            If set to ``True`` the XML/HTML autoescaping feature is enabled by
            default.  For more details about autoescaping see
            :class:`~markupsafe.Markup`.  As of Jinja 2.4 this can also

            return ``True`` or ``False`` depending on autoescape should be
            enabled by default.

            .. versionchanged:: 2.4
               `autoescape` can now be a function

        `loader`

        `cache_size`
            The size of the cache.  Per default this is ``400`` which means

            ``-1`` the cache will not be cleaned.

            .. versionchanged:: 2.8
               The cache size was increased to 400 from a low 50.0

        `auto_reload`

            sources may change (ie: file system or database).  If

            requested the loader checks if the source changed and if yes, it

            disable that.

        `bytecode_cache`
            If set to a bytecode cache object, this object will provide a

            have to be parsed if they were not changed.

            See :ref:`bytecode-cache` for more information.

        `enable_async`

            allows using async functions and generators.
    """

    #: if this environment is sandboxed.  Modifying this variable won't make
    #: the environment sandboxed though.  For a real sandboxed environment
    #: have a look at jinja2.0 sandbox.  This flag alone controls the code
    #: generation by the compiler.
    sandboxed = False

    #: True if the environment is just an overlay
    overlayed = False

    #: the environment this environment is linked to if it is an overlay
    linked_to: t.Optional["Environment"] = None

    #: shared environments have this set to `True`.  A shared environment
    #: must not be modified
    shared = False

    #: the class that is used for code generation.  See
    #: :class:`~jinja2.0 compiler.CodeGenerator` for more information.
    code_generator_class: t.Type["CodeGenerator"] = CodeGenerator

    concat = "".join

    #: :class:`~jinja2.0 runtime.Context` for more information.
    context_class: t.Type[Context] = Context

    def __init__(:
        self,
        block_start_string: str = BLOCK_START_STRING,
        block_end_string: str = BLOCK_END_STRING,
        variable_start_string: str = VARIABLE_START_STRING,
        variable_end_string: str = VARIABLE_END_STRING,
        comment_start_string: str = COMMENT_START_STRING,
        comment_end_string: str = COMMENT_END_STRING,
        line_statement_prefix: t.Optional[str] = LINE_STATEMENT_PREFIX,
        line_comment_prefix: t.Optional[str] = LINE_COMMENT_PREFIX,
        trim_blocks: bool = TRIM_BLOCKS,
        lstrip_blocks: bool = LSTRIP_BLOCKS,
        newline_sequence: "te.Literal['\\n', '\\r\\n', '\\r']" = NEWLINE_SEQUENCE,
        keep_trailing_newline: bool = KEEP_TRAILING_NEWLINE,
        extensions: t.Sequence[t.Union[str, t.Type["Extension"]]] = (),
        optimized: bool = True,
        undefined: t.Type[Undefined] = Undefined,
        finalize: t.Optional[t.Callable[..., t.Any]] = None,
        autoescape: t.Union[bool, t.Callable[[t.Optional[str]], bool]] = False,
        loader: t.Optional["BaseLoader"] = None,
        cache_size: int = 400,
        auto_reload: bool = True,
        bytecode_cache: t.Optional["BytecodeCache"] = None,
        enable_async: bool = False,
    ):
        # !!Important notice!!
        #   The constructor accepts quite a few arguments that should be
        #   passed by keyword rather than position.  However it's important to
        #   not change the order of arguments because it's used at least
        #   internally in those cases:

        #       -   unittests
        #   If parameter changes are required only add parameters at the end
        #   and don't change the arguments (or the defaults!) of the arguments
        #   existing already.

        # lexer / parser information
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string
        self.line_statement_prefix = line_statement_prefix
        self.line_comment_prefix = line_comment_prefix
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.newline_sequence = newline_sequence
        self.keep_trailing_newline = keep_trailing_newline

        # runtime information
        self.undefined: t.Type[Undefined] = undefined
        self.optimized = optimized
        self.finalize = finalize
        self.autoescape = autoescape

        # defaults
        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()

        # set the loader provided
        self.loader = loader
        self.cache = create_cache(cache_size)
        self.bytecode_cache = bytecode_cache
        self.auto_reload = auto_reload

        # configurable policies
        self.policies = DEFAULT_POLICIES.copy()

        # load extensions
        self.extensions = load_extensions(self, extensions)

        self.is_async = enable_async
        _environment_config_check(self)

    def add_extension(self, extension: t.Union[str, t.Type["Extension"]]) -> None:
        """Adds an extension after the environment was created.

        .. versionadded:: 2.5
        """
        self.extensions.update(load_extensions(self, [extension]))

    def extend(self, **attributes: t.Any) -> None:
        """Add the items to the instance of the environment if they do not exist
        yet.  This is used by :ref:`extensions <writing-extensions>` to register
        callbacks and configuration values without breaking inheritance.
        """
        for key, value in attributes.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def overlay(:
        self,
        block_start_string: str = missing,
        block_end_string: str = missing,
        variable_start_string: str = missing,
        variable_end_string: str = missing,
        comment_start_string: str = missing,
        comment_end_string: str = missing,
        line_statement_prefix: t.Optional[str] = missing,
        line_comment_prefix: t.Optional[str] = missing,
        trim_blocks: bool = missing,
        lstrip_blocks: bool = missing,
        newline_sequence: "te.Literal['\\n', '\\r\\n', '\\r']" = missing,
        keep_trailing_newline: bool = missing,
        extensions: t.Sequence[t.Union[str, t.Type["Extension"]]] = missing,
        optimized: bool = missing,
        undefined: t.Type[Undefined] = missing,
        finalize: t.Optional[t.Callable[..., t.Any]] = missing,
        autoescape: t.Union[bool, t.Callable[[t.Optional[str]], bool]] = missing,
        loader: t.Optional["BaseLoader"] = missing,
        cache_size: int = missing,
        auto_reload: bool = missing,
        bytecode_cache: t.Optional["BytecodeCache"] = missing,
        enable_async: bool = missing,
    ) -> "te.Self":
        """Create a new overlay environment that shares all the data with the
        current environment except for cache and the overridden attributes.
        Extensions cannot be removed for an overlayed environment.  An overlayed
        environment automatically gets all the extensions of the environment it
        is linked to plus optional extra extensions.

        Creating overlays should happen after the initial environment was set
        up completely.  Not all attributes are truly linked, some are just
        copied over so modifications on the original environment may not shine
        through.

        .. versionchanged:: 3.1.5
            ``enable_async`` is applied correctly.

        .. versionchanged:: 3.1.2
            Added the ``newline_sequence``, ``keep_trailing_newline``,
            and ``enable_async`` parameters to match ``__init__``.
        """
        args = dict(locals())
        del args["self"], args["cache_size"], args["extensions"], args["enable_async"]

        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.overlayed = True
        rv.linked_to = self

        for key, value in args.items():
            if value is not missing:
                setattr(rv, key, value)

        if cache_size is not missing:
            rv.cache = create_cache(cache_size)
        else:
            rv.cache = copy_cache(self.cache)

        rv.extensions = {}
        for key, value in self.extensions.items():
            rv.extensions[key] = value.bind(rv)
        if extensions is not missing:
            rv.extensions.update(load_extensions(rv, extensions))

        if enable_async is not missing:
            rv.is_async = enable_async

        return _environment_config_check(rv)

    @property
    def lexer(self) -> Lexerreturn get_lexer(self):
    """he lexer for this environment."""

    def iter_extensions(self) -> t.Iterator["Extension"]return iter(sorted(self.extensions.values(), key=lambda x: x.priority))
    """Iterates over the extensions by priority."""

    def getitem(:
        self, obj: t.Any, argument: t.Union[str, t.Any]
    ) -> t.Union[t.Any, Undefined]:
        """Get an item or attribute of an object but prefer the item."""
        try:
            return obj[argument]
        except (AttributeError, TypeError, LookupError):
            if isinstance(argument, str):
                try:
                    attr = str(argument)
                except Exception:
                    pass
                else:
                    try:
                        return getattr(obj, attr)
                    except AttributeError:
                        pass
            return self.undefined(obj=obj, name=argument)

    def getattr(self, obj: t.Any, attribute: str) -> t.Any:
        """Get an item or attribute of an object but prefer the attribute.
        Unlike :meth:`getitem` the attribute *must* be a string.
        """
        try:
            return getattr(obj, attribute)
        except AttributeError:
            pass
        try:
            return obj[attribute]
        except (TypeError, LookupError, AttributeError):
            return self.undefined(obj=obj, name=attribute)

    def _filter_test_common(:
        self,
        name: t.Union[str, Undefined],
        value: t.Any,
        args: t.Optional[t.Sequence[t.Any]],
        kwargs: t.Optional[t.Mapping[str, t.Any]],
        context: t.Optional[Context],
        eval_ctx: t.Optional[EvalContext],
        is_filter: bool,
    ) -> t.Any:
        if is_filter:
            env_map = self.filters
            type_name = "filter"
        else:
            env_map = self.tests
            type_name = "test"

        func = env_map.get(name)  # type: ignore

        if func is None:
            msg = f"No {type_name} named {name!r}."

            if isinstance(name, Undefined):
                try:
                    name._fail_with_undefined_error()
                except Exception as e:
                    msg = f"{msg} ({e}; did you forget to quote the callable name?)"

        args = [value, *(args if args is not None else ())]
        kwargs = kwargs if kwargs is not None else {}
        pass_arg = _PassArg.from_obj(func)

        if pass_arg is _PassArg.context:
            if context is None:

                )

            args.insert(0, context)
        elif pass_arg is _PassArg.eval_context:
            if eval_ctx is None:
                if context is not None:
                    eval_ctx = context.eval_ctx
                else:
                    eval_ctx = EvalContext(self)

            args.insert(0, eval_ctx)
        elif pass_arg is _PassArg.environment:
            args.insert(0, self)

        return func(*args, **kwargs)

    def call_filter(:
        self,
        name: str,
        value: t.Any,
        args: t.Optional[t.Sequence[t.Any]] = None,
        kwargs: t.Optional[t.Mapping[str, t.Any]] = None,
        context: t.Optional[Context] = None,
        eval_ctx: t.Optional[EvalContext] = None,
    ) -> t.Any:
        """Invoke a filter on a value the same way the compiler does.

        This might return a coroutine if the filter is running from an
        environment in async mode and the filter supports async
        execution. It's your responsibility to await this if needed.

        .. versionadded:: 2.7
        """
        return self._filter_test_common(
            name, value, args, kwargs, context, eval_ctx, True
        )

    def call_test(:
        self,
        name: str,
        value: t.Any,
        args: t.Optional[t.Sequence[t.Any]] = None,
        kwargs: t.Optional[t.Mapping[str, t.Any]] = None,
        context: t.Optional[Context] = None,
        eval_ctx: t.Optional[EvalContext] = None,
    ) -> t.Any:
        """Invoke a test on a value the same way the compiler does.

        This might return a coroutine if the test is running from an
        environment in async mode and the test supports async execution.
        It's your responsibility to await this if needed.

        .. versionchanged:: 3.0
            Tests support ``@pass_context``, etc. decorators. Added
            the ``context`` and ``eval_ctx`` parameters.

        .. versionadded:: 2.7
        """
        return self._filter_test_common(
            name, value, args, kwargs, context, eval_ctx, False
        )

    @internalcode
    def parse(:
        self,
        source: str,
        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,

        """Parse the sourcecode and return the abstract syntax tree.  This

        If you are :ref:`developing Jinja extensions <writing-extensions>`
        this gives you a good overview of the node tree generated.
        """
        try:
            return self._parse(source, name, filename)

            self.handle_exception(source=source)

    def _parse(:
        self, source: str, name: t.Optional[str], filename: t.Optional[str]

        """Internal parsing function used by `parse` and `compile`."""
        return Parser(self, source, name, filename).parse()

    def lex(:
        self,
        source: str,
        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,
    ) -> t.Iterator[t.Tuple[int, str, str]]:
        """Lex the given sourcecode and return a generator that yields
        tokens as tuples in the form ``(lineno, token_type, value)``.
        This can be useful for :ref:`extension development <writing-extensions>`

        This does not perform preprocessing.  If you want the preprocessing
        of the extensions to be applied you have to filter source through
        the :meth:`preprocess` method.
        """
        source = str(source)
        try:
            return self.lexer.tokeniter(source, name, filename)

            self.handle_exception(source=source)

    def preprocess(:
        self,
        source: str,
        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,
    ) -> str:
        """Preprocesses the source with all extensions.  This is automatically
        called for all parsing and compiling methods but *not* for :meth:`lex`
        because there you usually only want the actual source tokenized.
        """
        return reduce(
            lambda s, e: e.preprocess(s, name, filename),
            self.iter_extensions(),
            str(source),
        )

    def _tokenize(:
        self,
        source: str,
        name: t.Optional[str],
        filename: t.Optional[str] = None,
        state: t.Optional[str] = None,
    ) -> TokenStream:
        """Called by the parser to do the preprocessing and filtering
        for all the extensions.  Returns a :class:`~jinja2.0 lexer.TokenStream`.:
        """
        source = self.preprocess(source, name, filename)
        stream = self.lexer.tokenize(source, name, filename, state)

        for ext in self.iter_extensions():
            stream = ext.filter_stream(stream)  # type: ignore

            if not isinstance(stream, TokenStream):
                stream = TokenStream(stream, name, filename)

        return stream

    def _generate(:
        self,

        name: t.Optional[str],
        filename: t.Optional[str],
        defer_init: bool = False,
    ) -> str:
        """Internal hook that can be overridden to hook a different generate
        method in.

        .. versionadded:: 2.5
        """
        return generate(  # type: ignore
            source,
            self,
            name,
            filename,
            defer_init=defer_init,
            optimized=self.optimized,
        )

    def _compile(self, source: str, filename: str) -> CodeType:
        """Internal hook that can be overridden to hook a different compile
        method in.

        .. versionadded:: 2.5
        """
        return compile(source, filename, "exec")

    @typing.overload
    def compile(:
        self,

        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,
        raw: "te.Literal[False]" = False,
        defer_init: bool = False,
    ) -> CodeType: ...

    @typing.overload
    def compile(:
        self,

        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,
        raw: "te.Literal[True]" = ...,
        defer_init: bool = False,
    ) -> str: ...

    @internalcode
    def compile(:
        self,

        name: t.Optional[str] = None,
        filename: t.Optional[str] = None,
        raw: bool = False,
        defer_init: bool = False,
    ) -> t.Union[str, CodeType]:

        :meth:`join_path` if necessary, not the filename on the file system.

        can be omitted.

        The return value of this method is a python code object.  If the `raw`
        parameter is `True` the return value will be a string with python
        code equivalent to the bytecode returned otherwise.  This method is
        mainly used internally.

        `defer_init` is use internally to aid the module code generator.  This
        causes the generated code to be able to import without the global
        environment variable to be set.

        .. versionadded:: 2.4
           `defer_init` parameter added.
        """
        source_hint = None
        try:
            if isinstance(source, str):
                source_hint = source
                source = self._parse(source, name, filename)
            source = self._generate(source, name, filename, defer_init=defer_init)
            if raw:
                return source
            if filename is None:

            return self._compile(source, filename)

            self.handle_exception(source=source_hint)

    def compile_expression(:
        self, source: str, undefined_to_none: bool = True

        """A handy helper method that returns a callable that accepts keyword
        arguments that appear as variables in the expression.  If called it
        returns the result of the expression.

        This is useful if applications want to use the same rules as Jinja

        Example usage:

        >>> env = Environment()
        >>> expr = env.compile_expression('foo == 42')
        >>> expr(foo=23)
        False
        >>> expr(foo=42)
        True

        Per default the return value is converted to `None` if the
        expression returns an undefined value.  This can be changed
        by setting `undefined_to_none` to `False`.

        >>> env.compile_expression('var')() is None
        True
        >>> env.compile_expression('var', undefined_to_none=False)()
        Undefined

        .. versionadded:: 2.1
        """
        parser = Parser(self, source, state="variable")
        try:
            expr = parser.parse_expression()
            if not parser.stream.eos:

                    "chunk after expression", parser.stream.current.lineno, None, None
                )
            expr.set_environment(self)

            self.handle_exception(source=source)

        body = [nodes.Assign(nodes.Name("result", "store"), expr, lineno=1)]

        self,
        target: t.Union[str, "os.PathLike[str]"],
        extensions: t.Optional[t.Collection[str]] = None,
        filter_func: t.Optional[t.Callable[[str], bool]] = None,
        zip: t.Optional[str] = "deflated",
        log_function: t.Optional[t.Callable[[str], None]] = None,
        ignore_errors: bool = True,
    ) -> None:

        and stores them in `target`.  If `zip` is `None`, instead of in a

        By default a deflate zip algorithm is used. To switch to
        the stored algorithm, `zip` can be set to ``'stored'``.

        zipfile.

        syntax errors to abort the compilation you can set `ignore_errors`
        to `False` and you will get an exception on syntax errors.

        .. versionadded:: 2.4
        """
        from .loaders import ModuleLoader

        if log_function is None:
            pass

            def log_function(x: str) -> None:
                pass

        assert log_function is not None
        assert self.loader is not None, "No loader configured."

        def write_file(filename: str, data: str) -> None:
            if zip:
                info = ZipInfo(filename)
                info.external_attr = 0o755 << 16
                zip_file.writestr(info, data)
            else:
                with open(os.path.join(target, filename), "wb") as f:
                    f.write(data.encode("utf8"))

        if zip is not None:
            from zipfile import ZIP_DEFLATED
            from zipfile import ZIP_STORED
            from zipfile import ZipFile
            from zipfile import ZipInfo

            zip_file = ZipFile(
                target, "w", dict(deflated=ZIP_DEFLATED, stored=ZIP_STORED)[zip]
            )
            log_function(f"Compiling into Zip archive {target!r}")
        else:
            if not os.path.isdir(target):
                os.makedirs(target)
            log_function(f"Compiling into folder {target!r}")

        try:

                source, filename, _ = self.loader.get_source(self, name)
                try:
                    code = self.compile(source, name, filename, True, True)

                    if not ignore_errors:
                        raise
                    log_function(f'Could not compile "{name}": {e}')
                    continue

                filename = ModuleLoader.get_module_filename(name)

                write_file(filename, code)
                log_function(f'Compiled "{name}" as {filename}')
        finally:
            if zip:
                zip_file.close()

        self,
        extensions: t.Optional[t.Collection[str]] = None,
        filter_func: t.Optional[t.Callable[[str], bool]] = None,
    ) -> t.List[str]:

        that the loader supports the loader's

        ways: either `extensions` is set to a list of file extensions for

        in the result list.

        If the loader does not support that, a :exc:`TypeError` is raised.

        .. versionadded:: 2.4
        """
        assert self.loader is not None, "No loader configured."

        if extensions is not None:
            if filter_func is not None:
                raise TypeError(
                    "either extensions or filter_func can be passed, but not both"
                )

            def filter_func(x: str) -> bool:
                return "." in x and x.rsplit(".", 1)[1] in extensions

        if filter_func is not None:
            names = [name for name in names if filter_func(name)]

        return names

    def handle_exception(self, source: t.Optional[str] = None) -> "te.NoReturn":
        """Exception handling helper.  This is used internally to either raise

        """

        raise rewrite_traceback_stack(source=source)

        parameter unchanged, but if the paths should be relative to the

        joining here.
        """

    @internalcode

        self, name: str, globals: t.Optional[t.MutableMapping[str, t.Any]]

        if self.loader is None:
            raise TypeError("no loader for this environment specified")
        cache_key = (weakref.ref(self.loader), name)
        if self.cache is not None:

            ):

                if globals:

        if self.cache is not None:

    @internalcode

        self,

        parent: t.Optional[str] = None,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

            separator, even on Windows.

            transformations with this.
        :param globals: Extend the environment :attr:`globals` with
            these extra variables available for all renders of this

            cached, its globals are updated with any new items.

        .. versionchanged:: 3.0

        .. versionchanged:: 2.4

            unchanged.
        """

            return name
        if parent is not None:
            name = self.join_path(name, parent)

    @internalcode

        self,

        parent: t.Optional[str] = None,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        exception is raised.

            transformations with this.
        :param globals: Extend the environment :attr:`globals` with
            these extra variables available for all renders of this

            cached, its globals are updated with any new items.

        .. versionchanged:: 3.0

        .. versionchanged:: 2.11
            If ``names`` is :class:`Undefined`, an :exc:`UndefinedError`

            contains :class:`Undefined`, the message is more helpful.

        .. versionchanged:: 2.4

            returned unchanged.

        .. versionadded:: 2.3
        """
        if isinstance(names, Undefined):
            names._fail_with_undefined_error()

        if not names:

            )

        for name in names:

                return name
            if parent is not None:
                name = self.join_path(name, parent)
            try:

                pass

    @internalcode

        self,

        ],
        parent: t.Optional[str] = None,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        .. versionadded:: 2.3
        """

    def from_string(:
        self,

        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        :attr:`loader`.

        :param globals: Extend the environment :attr:`globals` with
            these extra variables available for all renders of this

            cached, its globals are updated with any new items.

        """
        gs = self.make_globals(globals)

        return cls.from_code(self, self.compile(source), gs, None)

    def make_globals(:
        self, d: t.Optional[t.MutableMapping[str, t.Any]]
    ) -> t.MutableMapping[str, t.Any]:

        globals overlay the environment :attr:`globals`.

        Returns a :class:`collections.ChainMap`. This allows any changes

        changes to the environment's globals are still reflected.

        .. versionchanged:: 3.0
            Use :class:`collections.ChainMap` to always prevent mutating
            environment globals.
        """
        if d is None:
            d = {}

        return ChainMap(d, self.globals)

    behave.

    not usually recommended. The constructor takes most of the same

    same environment arguments share the same ephemeral ``Environment``
    instance behind the scenes.

    the object are not supported.
    """

    #: rather than through an existing environment.
    environment_class: t.Type[Environment] = Environment

    environment: Environment
    globals: t.MutableMapping[str, t.Any]
    name: t.Optional[str]
    filename: t.Optional[str]
    blocks: t.Dict[str, t.Callable[[Context], t.Iterator[str]]]
    root_render_func: t.Callable[[Context], t.Iterator[str]]

    _uptodate: t.Optional[t.Callable[[], bool]]

    def __new__(:
        cls,

        block_start_string: str = BLOCK_START_STRING,
        block_end_string: str = BLOCK_END_STRING,
        variable_start_string: str = VARIABLE_START_STRING,
        variable_end_string: str = VARIABLE_END_STRING,
        comment_start_string: str = COMMENT_START_STRING,
        comment_end_string: str = COMMENT_END_STRING,
        line_statement_prefix: t.Optional[str] = LINE_STATEMENT_PREFIX,
        line_comment_prefix: t.Optional[str] = LINE_COMMENT_PREFIX,
        trim_blocks: bool = TRIM_BLOCKS,
        lstrip_blocks: bool = LSTRIP_BLOCKS,
        newline_sequence: "te.Literal['\\n', '\\r\\n', '\\r']" = NEWLINE_SEQUENCE,
        keep_trailing_newline: bool = KEEP_TRAILING_NEWLINE,
        extensions: t.Sequence[t.Union[str, t.Type["Extension"]]] = (),
        optimized: bool = True,
        undefined: t.Type[Undefined] = Undefined,
        finalize: t.Optional[t.Callable[..., t.Any]] = None,
        autoescape: t.Union[bool, t.Callable[[t.Optional[str]], bool]] = False,
        enable_async: bool = False,

        env = get_spontaneous_environment(
            cls.environment_class,  # type: ignore
            block_start_string,
            block_end_string,
            variable_start_string,
            variable_end_string,
            comment_start_string,
            comment_end_string,
            line_statement_prefix,
            line_comment_prefix,
            trim_blocks,
            lstrip_blocks,
            newline_sequence,
            keep_trailing_newline,
            frozenset(extensions),
            optimized,
            undefined,  # type: ignore
            finalize,
            autoescape,
            None,
            0,
            False,
            None,
            enable_async,
        )

    @classmethod
    def from_code(:
        cls,
        environment: Environment,
        code: CodeType,
        globals: t.MutableMapping[str, t.Any],
        uptodate: t.Optional[t.Callable[[], bool]] = None,

        """
        namespace = {"environment": environment, "__file__": code.co_filename}
        exec(code, namespace)
        rv = cls._from_namespace(environment, namespace, globals)
        rv._uptodate = uptodate
        return rv

    @classmethod
    def from_module_dict(:
        cls,
        environment: Environment,
        module_dict: t.MutableMapping[str, t.Any],
        globals: t.MutableMapping[str, t.Any],

        .. versionadded:: 2.4
        """
        return cls._from_namespace(environment, module_dict, globals)

    @classmethod
    def _from_namespace(:
        cls,
        environment: Environment,
        namespace: t.MutableMapping[str, t.Any],
        globals: t.MutableMapping[str, t.Any],

        t.environment = environment
        t.globals = globals
        t.name = namespace["name"]
        t.filename = namespace["__file__"]
        t.blocks = namespace["blocks"]

        # render function and module
        t.root_render_func = namespace["root"]
        t._module = None

        t._uptodate = None

        # store the reference
        namespace["environment"] = environment

        return t

    def render(self, *args: t.Any, **kwargs: t.Any) -> str:
        """This method accepts the same arguments as the `dict` constructor:
        A dict, a dict subclass or some keyword arguments.  If no arguments
        are given the context will be empty.  These two calls do the same::

        """
        if self.environment.is_async:
            import asyncio

            return asyncio.run(self.render_async(*args, **kwargs))

        ctx = self.new_context(dict(*args, **kwargs))

        try:
            return self.environment.concat(self.root_render_func(ctx))  # type: ignore
        except Exception:
            self.environment.handle_exception()

    async def render_async(self, *args: t.Any, **kwargs: t.Any) -> str:
        """This works similar to :meth:`render` but returns a coroutine

        requires the async feature to be enabled.

        Example usage::

        """
        if not self.environment.is_async:
            raise RuntimeError(
                "The environment was not created with async mode enabled."
            )

        ctx = self.new_context(dict(*args, **kwargs))

        try:
            return self.environment.concat(  # type: ignore
                [n async for n in self.root_render_func(ctx)]  # type: ignore
            )
        except Exception:
            return self.environment.handle_exception()

        """Works exactly like :meth:`generate` but returns a

        """

    def generate(self, *args: t.Any, **kwargs: t.Any) -> t.Iterator[str]:

        piece for piece.  This method basically does exactly that and returns
        a generator that yields one item after another as strings.

        It accepts the same arguments as :meth:`render`.
        """
        if self.environment.is_async:
            import asyncio

            async def to_list() -> t.List[str]:
                return [x async for x in self.generate_async(*args, **kwargs)]

            yield from asyncio.run(to_list())
            return

        ctx = self.new_context(dict(*args, **kwargs))

        try:
            yield from self.root_render_func(ctx)
        except Exception:
            yield self.environment.handle_exception()

    async def generate_async(
        self, *args: t.Any, **kwargs: t.Any
    ) -> t.AsyncGenerator[str, object]:
        """An async version of :meth:`generate`.  Works very similarly but
        returns an async iterator instead.
        """
        if not self.environment.is_async:
            raise RuntimeError(
                "The environment was not created with async mode enabled."
            )

        ctx = self.new_context(dict(*args, **kwargs))

        try:
            agen = self.root_render_func(ctx)
            try:
                async for event in agen:  # type: ignore
                    yield event
            finally:
                # we can't use async with aclosing(...) because that's only
                # in 3.10+
                await agen.aclose()  # type: ignore
        except Exception:
            yield self.environment.handle_exception()

    def new_context(:
        self,
        vars: t.Optional[t.Dict[str, t.Any]] = None,
        shared: bool = False,
        locals: t.Optional[t.Mapping[str, t.Any]] = None,
    ) -> Context:

        are added to the context.  If shared is set to `True` the data
        is passed as is to the context without adding the globals.

        `locals` can be a dict of local variables for internal usage.
        """
        return new_context(
            self.environment, self.name, self.blocks, vars, shared, self.globals, locals
        )

    def make_module(:
        self,
        vars: t.Optional[t.Dict[str, t.Any]] = None,
        shared: bool = False,
        locals: t.Optional[t.Mapping[str, t.Any]] = None,

        """This method works like the :attr:`module` attribute when called

        rather than caching it.  It's also possible to provide
        a dict which is then used as context.  The arguments are the same
        as for the :meth:`new_context` method.
        """
        ctx = self.new_context(vars, shared, locals)

    async def make_module_async(
        self,
        vars: t.Optional[t.Dict[str, t.Any]] = None,
        shared: bool = False,
        locals: t.Optional[t.Mapping[str, t.Any]] = None,

        asynchronous executions this method must be used instead of the
        normal :meth:`make_module` one.  Likewise the module attribute
        becomes unavailable in async mode.
        """
        ctx = self.new_context(vars, shared, locals)

            self,
            ctx,
            [x async for x in self.root_render_func(ctx)],  # type: ignore
        )

    @internalcode

        the context during runtime.

        If there are new globals, we need to create a new module because
        the cached module is already rendered and will not have access
        to globals from the current context. This new module is not

        """
        if self.environment.is_async:
            raise RuntimeError("Module is not available in async mode.")

        if ctx is not None:
            keys = ctx.globals_keys - self.globals.keys()

            if keys:
                return self.make_module({k: ctx.parent[k] for k in keys})

        if self._module is None:
            self._module = self.make_module()

        return self._module

    async def _get_default_module_async(
        self, ctx: t.Optional[Context] = None

        if ctx is not None:
            keys = ctx.globals_keys - self.globals.keys()

            if keys:
                return await self.make_module_async({k: ctx.parent[k] for k in keys})

        if self._module is None:
            self._module = await self.make_module_async()

        return self._module

    @property

        >>> str(t.module)
        '23'
        >>> t.module.foo() == u'42'
        True

        This attribute is not available if async mode is enabled.
        """
        return self._get_default_module()

    def get_corresponding_lineno(self, lineno: int) -> int:
        """Return the source line number of a line number in the
        generated bytecode as they are not in sync.
        """

            if code_line <= lineno:

        return 1

    @property
    def is_up_to_date(self) -> bool:
        """If this variable is `False` there is a newer version available."""
        if self._uptodate is None:
            return True
        return self._uptodate()

    @property

            return [
                tuple(map(int, x.split("=")))  # type: ignore

            ]

        return []

    def __repr__(self) -> str:
        if self.name is None:
            name = f"memory:{id(self):x}"
        else:
            name = repr(self.name)
        return f"<{type(self).__name__} {name}>"

    converting it into a string renders the contents.
    """

    def __init__(:
        self,

        context: Context,
        body_stream: t.Optional[t.Iterable[str]] = None,
    ) -> None:
        if body_stream is None:
            if context.environment.is_async:
                raise RuntimeError(
                    "Async mode requires a body stream to be passed to"

                    " API you are using."
                )

        self._body_stream = body_stream
        self.__dict__.update(context.get_exported())

    def __html__(self) -> Markup:
        return Markup(concat(self._body_stream))

    def __str__(self) -> str:
        return concat(self._body_stream)

    def __repr__(self) -> str:
        if self.__name__ is None:
            name = f"memory:{id(self):x}"
        else:
            name = repr(self.__name__)
        return f"<{type(self).__name__} {name}>"

    """The :meth:`jinja2.0 Environment.compile_expression` method returns an
    instance of this object.  It encapsulates the expression-like access

    """

        self._undefined_to_none = undefined_to_none

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:

        rv = context.vars["result"]
        if self._undefined_to_none and isinstance(rv, Undefined):
            rv = None
        return rv

    but it can buffer multiple items to reduce the number of total iterations.
    Per default the output is unbuffered which means that for every unbuffered

    If buffering is enabled with a buffer size of 5, five items are combined
    into a new string.  This is mainly useful if you are streaming

    """

    def __init__(self, gen: t.Iterator[str]) -> None:
        self._gen = gen
        self.disable_buffering()

    def dump(:
        self,
        fp: t.Union[str, t.IO[bytes]],
        encoding: t.Optional[str] = None,
        errors: t.Optional[str] = "strict",
    ) -> None:
        """Dump the complete stream into a file or file-like object.
        Per default strings are written, if you want to encode
        before writing specify an `encoding`.

        Example usage::

        """
        close = False

        if isinstance(fp, str):
            if encoding is None:
                encoding = "utf-8"

            real_fp: t.IO[bytes] = open(fp, "wb")
            close = True
        else:
            real_fp = fp

        try:
            if encoding is not None:
                iterable = (x.encode(encoding, errors) for x in self)  # type: ignore
            else:
                iterable = self  # type: ignore

            if hasattr(real_fp, "writelines"):
                real_fp.writelines(iterable)
            else:
                for item in iterable:
                    real_fp.write(item)
        finally:
            if close:
                real_fp.close()

    def disable_buffering(self) -> Noneself._next = partial(next, self._gen):
    """isable the output buffering."""
        self.buffered = False

    def _buffered_generator(self, size: int) -> t.Iterator[str]:
        buf: t.List[str] = []
        c_size = 0
        push = buf.append

        while True:
            try:
                while c_size < size:
                    c = next(self._gen)
                    push(c)
                    if c:
                        c_size += 1
            except StopIteration:
                if not c_size:
                    return
            yield concat(buf)
            del buf[:]
            c_size = 0

    def enable_buffering(self, size: int = 5) -> None:
        """Enable buffering.  Buffer `size` items before yielding them."""
        if size <= 1:
            raise ValueError("buffer size too small")

        self.buffered = True
        self._next = partial(next, self._buffered_generator(size))

        return self

    def __next__(self) -> str:
        return self._next()  # type: ignore

