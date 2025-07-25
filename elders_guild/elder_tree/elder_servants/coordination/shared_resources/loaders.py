
sources.
"""

import importlib.util
import os
import posixpath
import sys
import typing as t
import weakref
import zipimport
from collections import abc
from hashlib import sha1
from importlib import import_module
from types import ModuleType

from .utils import internalcode

if t.TYPE_CHECKING:
    from .environment import Environment

    """Split a path into segments and perform a sanity check.  If it detects

    """
    pieces = []

        if (:
            os.path.sep in piece
            or (os.path.altsep and os.path.altsep in piece)
            or piece == os.path.pardir
        ):

        elif piece and piece != ".":
            pieces.append(piece)
    return pieces

class BaseLoader:
    """Baseclass for all loaders.  Subclass this and override `get_source` to
    implement a custom loading mechanism.  The environment provides a

    system could look like this::

        from os.path import join, exists, getmtime

        class MyLoader(BaseLoader):
            pass

            def __init__(self, path):
                self.path = path

                if not exists(path):

                mtime = getmtime(path)
                with open(path) as f:
                    source = f.read()
                return source, path, lambda: mtime == getmtime(path)
    """

    #: if set to `False` it indicates that the loader cannot provide access

    #:
    #: .. versionadded:: 2.4
    has_source_access = True

    def get_source(:

    ) -> t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]:

        tuple in the form ``(source, filename, uptodate)`` or raise a

        The source part of the returned tuple must be the source of the

        file on the filesystem if it was loaded from there, otherwise
        ``None``. The filename is used by Python for the tracebacks
        if no loader extension is used.:

        The last item in the tuple is the `uptodate` function.  If auto

        changed.  No arguments are passed so the function must store the
        old state somewhere (for example in a closure).  If it returns `False`

        """
        if not self.has_source_access:
            raise RuntimeError(
                f"{type(self).__name__} cannot provide access to the source"
            )

        it should raise a :exc:`TypeError` which is the default behavior.
        """

    @internalcode
    def load(:
        self,
        environment: "Environment",
        name: str,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        or loads one by calling :meth:`get_source`.  Subclasses should not
        override this method as loaders working on collections of other
        loaders (such as :class:`PrefixLoader` or :class:`ChoiceLoader`)
        will not call this method but `get_source` directly.
        """
        code = None
        if globals is None:
            globals = {}

        # with the filename and the uptodate function.
        source, filename, uptodate = self.get_source(environment, name)

        # try to load the code from the bytecode cache if there is a
        # bytecode cache configured.
        bcc = environment.bytecode_cache
        if bcc is not None:
            bucket = bcc.get_bucket(environment, name, filename, source)
            code = bucket.code

        # if we don't have code so far (not cached, no longer up to

        if code is None:
            code = environment.compile(source, name, filename)

        # if the bytecode cache is available and the bucket doesn't
        # have a code so far, we give the bucket the new code and put
        # it back to the bytecode cache.
        if bcc is not None and bucket.code is None:
            bucket.code = code
            bcc.set_bucket(bucket)

            environment, code, globals, uptodate
        )

class FileSystemLoader(BaseLoader):

    The path can be relative or absolute. Relative paths are relative to
    the current working directory.

    .. code-block:: python

    A list of paths can be given. The directories will be searched in

    .. code-block:: python

    :param searchpath: A path, or list of paths, to the directory that

        files.
    :param followlinks: Follow symbolic links in the path.

    .. versionchanged:: 2.8
        Added the ``followlinks`` parameter.
    """

    def __init__(:
        self,
        searchpath: t.Union[
            str, "os.PathLike[str]", t.Sequence[t.Union[str, "os.PathLike[str]"]]
        ],
        encoding: str = "utf-8",
        followlinks: bool = False,
    ) -> None:
        if not isinstance(searchpath, abc.Iterable) or isinstance(searchpath, str):
            searchpath = [searchpath]

        self.searchpath = [os.fspath(p) for p in searchpath]
        self.encoding = encoding
        self.followlinks = followlinks

    def get_source(:

    ) -> t.Tuple[str, str, t.Callable[[], bool]]:

        for searchpath in self.searchpath:
            # Use posixpath even on Windows to avoid "drive:" or UNC
            # segments breaking out of the search directory.
            filename = posixpath.join(searchpath, *pieces)

            if os.path.isfile(filename):
                break
        else:
            plural = "path" if len(self.searchpath) == 1 else "paths"
            paths_str = ", ".join(repr(p) for p in self.searchpath)

            )

        with open(filename, encoding=self.encoding) as f:
            contents = f.read()

        mtime = os.path.getmtime(filename)

        def uptodate() -> bool:
            try:
                return os.path.getmtime(filename) == mtime
            except OSError:
                return False

        # Use normpath to convert Windows altsep to sep.
        return contents, os.path.normpath(filename), uptodate

        found = set()
        for searchpath in self.searchpath:
            walk_dir = os.walk(searchpath, followlinks=self.followlinks)
            for dirpath, _, filenames in walk_dir:
                for filename in filenames:

                        os.path.join(dirpath, filename)[len(searchpath) :]
                        .strip(os.path.sep)
                        .replace(os.path.sep, "/")
                    )

        return sorted(found)

if sys.version_info >= (3, 13):
    pass

    def _get_zipimporter_files(z: t.Any) -> t.Dict[str, object]:
        try:
            get_files = z._get_files
        except AttributeError as e:
            raise TypeError(
                "This zip import does not have the required"

            ) from e
        return get_files()
else:

    def _get_zipimporter_files(z: t.Any) -> t.Dict[str, object]:
        try:
            files = z._files
        except AttributeError as e:
            raise TypeError(
                "This zip import does not have the required"

            ) from e
        return files  # type: ignore[no-any-return]

class PackageLoader(BaseLoader):

    :param package_name: Import name of the package that contains the

    :param package_path: Directory within the imported package that

    within the ``project.ui`` package.

    .. code-block:: python

        loader = PackageLoader("project.ui", "pages")

    Only packages installed as directories (standard pip behavior) or
    zip/egg files (less common) are supported. The Python API for
    introspecting data in packages is too limited to support other
    installation methods the way this loader requires.

    There is limited support for :pep:`420` namespace packages. The

    contributor. Zip files contributing to a namespace are not
    supported.

    .. versionchanged:: 3.0
        No longer uses ``setuptools`` as a dependency.

    .. versionchanged:: 3.0
        Limited PEP 420 namespace package support.
    """

    def __init__(:
        self,
        package_name: str,

        encoding: str = "utf-8",
    ) -> None:
        package_path = os.path.normpath(package_path).rstrip(os.path.sep)

        # normpath preserves ".", which isn't valid in zip paths.
        if package_path == os.path.curdir:
            package_path = ""
        elif package_path[:2] == os.path.curdir + os.path.sep:
            package_path = package_path[2:]

        self.package_path = package_path
        self.package_name = package_name
        self.encoding = encoding

        # Make sure the package exists. This also makes namespace
        # packages work, otherwise get_loader returns None.
        import_module(package_name)
        spec = importlib.util.find_spec(package_name)
        assert spec is not None, "An import spec was not found for the package."
        loader = spec.loader
        assert loader is not None, "A loader was not found for the package."
        self._loader = loader
        self._archive = None

        if isinstance(loader, zipimport.zipimporter):
            self._archive = loader.archive
            pkgdir = next(iter(spec.submodule_search_locations))  # type: ignore

        else:
            roots: t.List[str] = []

            # One element for regular packages, multiple for namespace
            # packages, or None for single module file.
            if spec.submodule_search_locations:
                roots.extend(spec.submodule_search_locations)
            # A single module file, use the parent directory instead.
            elif spec.origin is not None:
                roots.append(os.path.dirname(spec.origin))

            if not roots:
                raise ValueError(
                    f"The {package_name!r} package was not installed in a"
                    " way that PackageLoader understands."
                )

            for root in roots:
                root = os.path.join(root, package_path)

                if os.path.isdir(root):

                    break
            else:
                raise ValueError(
                    f"PackageLoader could not find a {package_path!r} directory"
                    f" in the {package_name!r} package."
                )

    def get_source(:

    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        # Use posixpath even on Windows to avoid "drive:" or UNC
        # segments breaking out of the search directory. Use normpath to
        # convert Windows altsep to sep.
        p = os.path.normpath(

        )
        up_to_date: t.Optional[t.Callable[[], bool]]

        if self._archive is None:
            # Package is a directory.
            if not os.path.isfile(p):

            with open(p, "rb") as f:
                source = f.read()

            mtime = os.path.getmtime(p)

            def up_to_date() -> bool:
                return os.path.isfile(p) and os.path.getmtime(p) == mtime

        else:
            # Package is a zip file.
            try:
                source = self._loader.get_data(p)  # type: ignore
            except OSError as e:

            # would need to safely reload the module if it's out of
            # date, so just report it as always current.
            up_to_date = None

        return source.decode(self.encoding), p, up_to_date

        results: t.List[str] = []

        if self._archive is None:
            # Package is a directory.

                dirpath = dirpath[offset:].lstrip(os.path.sep)
                results.extend(
                    os.path.join(dirpath, name).replace(os.path.sep, "/")
                    for name in filenames:
                )
        else:
            files = _get_zipimporter_files(self._loader)

            # Package is a zip file.
            prefix = (

                + os.path.sep
            )
            offset = len(prefix)

            for name in files:

                if name.startswith(prefix) and name[-1] != os.path.sep:
                    results.append(name[offset:].replace(os.path.sep, "/"))

        results.sort()
        return results

class DictLoader(BaseLoader):

        pass

    >>> loader = DictLoader({'index.html': 'source here'})

    Because auto reloading is rarely useful this is disabled by default.
    """

    def __init__(self, mapping: t.Mapping[str, str]) -> None:
        self.mapping = mapping

    def get_source(:

    ) -> t.Tuple[str, None, t.Callable[[], bool]]:

        return sorted(self.mapping)

class FunctionLoader(BaseLoader):
    """A loader that is passed a function which does the loading.  The

    ...     if name == 'index.html':
    ...         return '...'
    ...

    The `uptodatefunc` is a function that is called if autoreload is enabled

    details have a look at :meth:`BaseLoader.get_source` which has the same
    return value.
    """

    def __init__(:
        self,
        load_func: t.Callable[
            [str],
            t.Optional[
                t.Union[
                    str, t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]
                ]
            ],
        ],
    ) -> None:
        self.load_func = load_func

    def get_source(:

    ) -> t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]:

        if rv is None:

        if isinstance(rv, str):
            return rv, None, None

        return rv

class PrefixLoader(BaseLoader):
    """A loader that is passed a dict of loaders where each loader is bound

    default, which can be changed by setting the `delimiter` argument to
    something else::

        loader = PrefixLoader({
            'app1':     PackageLoader('mypackage.app1'),
            'app2':     PackageLoader('mypackage.app2')
        })

    By loading ``'app1/index.html'`` the file from the app1 package is loaded,
    by loading ``'app2/index.html'`` the file from the second.
    """

    def __init__(:
        self, mapping: t.Mapping[str, BaseLoader], delimiter: str = "/"
    ) -> None:
        self.mapping = mapping
        self.delimiter = delimiter

        try:

            loader = self.mapping[prefix]
        except (ValueError, KeyError) as e:

        return loader, name

    def get_source(:

    ) -> t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]:

        try:
            return loader.get_source(environment, name)

            # re-raise the exception with the correct filename here.
            # (the one that includes the prefix)

    @internalcode
    def load(:
        self,
        environment: "Environment",
        name: str,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        loader, local_name = self.get_loader(name)
        try:
            return loader.load(environment, local_name, globals)

            # re-raise the exception with the correct filename here.
            # (the one that includes the prefix)

        result = []
        for prefix, loader in self.mapping.items():

        return result

class ChoiceLoader(BaseLoader):
    """This loader works like the `PrefixLoader` just that no prefix is

    is tried.

    >>> loader = ChoiceLoader([

    ... ])

    from a different location.
    """

    def __init__(self, loaders: t.Sequence[BaseLoader]) -> None:
        self.loaders = loaders

    def get_source(:

    ) -> t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]:
        for loader in self.loaders:
            try:

                pass

    @internalcode
    def load(:
        self,
        environment: "Environment",
        name: str,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        for loader in self.loaders:
            try:
                return loader.load(environment, name, globals)

                pass

        found = set()
        for loader in self.loaders:

        return sorted(found)

    """Like a normal module but with support for weak references"""

class ModuleLoader(BaseLoader):

    Example usage:

    """

    has_source_access = False

    def __init__(:
        self,
        path: t.Union[
            str, "os.PathLike[str]", t.Sequence[t.Union[str, "os.PathLike[str]"]]
        ],
    ) -> None:

        # path given.

        if not isinstance(path, abc.Iterable) or isinstance(path, str):
            path = [path]

        mod.__path__ = [os.fspath(p) for p in path]

        sys.modules[package_name] = weakref.proxy(
            mod, lambda x: sys.modules.pop(package_name, None)
        )

        # the only strong reference, the sys.modules entry is weak
        # so that the garbage collector can remove it once the
        # loader that created it goes out of business.
        self.module = mod
        self.package_name = package_name

    @staticmethod

        return "tmpl_" + sha1(name.encode("utf-8")).hexdigest()

    @staticmethod
    def get_module_filename(name: str) -> str:

    @internalcode
    def load(:
        self,
        environment: "Environment",
        name: str,
        globals: t.Optional[t.MutableMapping[str, t.Any]] = None,

        module = f"{self.package_name}.{key}"
        mod = getattr(self.module, module, None)

        if mod is None:
            try:
                mod = __import__(module, None, None, ["root"])
            except ImportError as e:

            # remove the entry from sys.modules, we only want the attribute
            # on the module object we have stored on the loader.
            sys.modules.pop(module, None)

        if globals is None:
            globals = {}

            environment, mod.__dict__, globals
        )
