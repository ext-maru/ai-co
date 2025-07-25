from __future__ import annotations

import os
import sys

from collections.abc import Iterable
from io import BytesIO, TextIOWrapper
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Generic,
    overload,
)

from .. import to_thread
from .._core._fileio import AsyncFile
from ..lowlevel import checkpoint_if_cancelled

if TYPE_CHECKING:
    from _typeshed import OpenBinaryMode, OpenTextMode, ReadableBuffer, WriteableBuffer

    """

    background thread, and is wrapped as an asynchronous file using `AsyncFile`.

    :param mode: The mode in which the file is opened. Defaults to "w+b".
    :param buffering: The buffering policy (-1 means the default buffering).
    :param encoding: The encoding used to decode or encode the file. Only applicable in
        text mode.
    :param newline: Controls how universal newlines mode works (only applicable in text
        mode).

    :param errors: The error handling scheme used for encoding/decoding errors.
    """

    _async_file: AsyncFile[AnyStr]

    @overload
    def __init__(:

        mode: OpenBinaryMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        *,
        errors: str | None = ...,
    ): ...
    @overload
    def __init__(:

        mode: OpenTextMode,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        *,
        errors: str | None = ...,
    ): ...

    def __init__(:
        self,
        mode: OpenTextMode | OpenBinaryMode = "w+b",
        buffering: int = -1,
        encoding: str | None = None,
        newline: str | None = None,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
        *,
        errors: str | None = None,
    ) -> None:
        self.mode = mode
        self.buffering = buffering
        self.encoding = encoding
        self.newline = newline
        self.suffix: str | None = suffix
        self.prefix: str | None = prefix
        self.dir: str | None = dir
        self.errors = errors

    async def __aenter__(self) -> AsyncFile[AnyStr]:
        fp = await to_thread.run_sync(

                self.mode,
                self.buffering,
                self.encoding,
                self.newline,
                self.suffix,
                self.prefix,
                self.dir,
                errors=self.errors,
            )
        )
        self._async_file = AsyncFile(fp)
        return self._async_file

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._async_file.aclose()

    """

    visible name in the file system. It uses Python's standard

    :class:`AsyncFile` for asynchronous operations.

    :param mode: The mode in which the file is opened. Defaults to "w+b".
    :param buffering: The buffering policy (-1 means the default buffering).
    :param encoding: The encoding used to decode or encode the file. Only applicable in
        text mode.
    :param newline: Controls how universal newlines mode works (only applicable in text
        mode).

    :param delete: Whether to delete the file when it is closed.
    :param errors: The error handling scheme used for encoding/decoding errors.
    :param delete_on_close: (Python 3.12+) Whether to delete the file on close.
    """

    _async_file: AsyncFile[AnyStr]

    @overload
    def __init__(:

        mode: OpenBinaryMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        delete: bool = ...,
        *,
        errors: str | None = ...,
        delete_on_close: bool = ...,
    ): ...
    @overload
    def __init__(:

        mode: OpenTextMode,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        delete: bool = ...,
        *,
        errors: str | None = ...,
        delete_on_close: bool = ...,
    ): ...

    def __init__(:
        self,
        mode: OpenBinaryMode | OpenTextMode = "w+b",
        buffering: int = -1,
        encoding: str | None = None,
        newline: str | None = None,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
        delete: bool = True,
        *,
        errors: str | None = None,
        delete_on_close: bool = True,
    ) -> None:
        self._params: dict[str, Any] = {
            "mode": mode,
            "buffering": buffering,
            "encoding": encoding,
            "newline": newline,
            "suffix": suffix,
            "prefix": prefix,
            "dir": dir,
            "delete": delete,
            "errors": errors,
        }
        if sys.version_info >= (3, 12):
            self._params["delete_on_close"] = delete_on_close

    async def __aenter__(self) -> AsyncFile[AnyStr]:
        fp = await to_thread.run_sync(

        )
        self._async_file = AsyncFile(fp)
        return self._async_file

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._async_file.aclose()

    """

    write operations and provides a method to force a rollover to disk.

    :param max_size: Maximum size in bytes before the file is rolled over to disk.
    :param mode: The mode in which the file is opened. Defaults to "w+b".
    :param buffering: The buffering policy (-1 means the default buffering).
    :param encoding: The encoding used to decode or encode the file (text mode only).
    :param newline: Controls how universal newlines mode works (text mode only).

    :param errors: The error handling scheme used for encoding/decoding errors.
    """

    _rolled: bool = False

    @overload
    def __init__(:

        max_size: int = ...,
        mode: OpenBinaryMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        *,
        errors: str | None = ...,
    ): ...
    @overload
    def __init__(:

        max_size: int = ...,
        mode: OpenTextMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        newline: str | None = ...,
        suffix: str | None = ...,
        prefix: str | None = ...,
        dir: str | None = ...,
        *,
        errors: str | None = ...,
    ): ...

    def __init__(:
        self,
        max_size: int = 0,
        mode: OpenBinaryMode | OpenTextMode = "w+b",
        buffering: int = -1,
        encoding: str | None = None,
        newline: str | None = None,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
        *,
        errors: str | None = None,
    ) -> None:

            "mode": mode,
            "buffering": buffering,
            "encoding": encoding,
            "newline": newline,
            "suffix": suffix,
            "prefix": prefix,
            "dir": dir,
            "errors": errors,
        }
        self._max_size = max_size
        if "b" in mode:
            super().__init__(BytesIO())  # type: ignore[arg-type]
        else:
            super().__init__(
                TextIOWrapper(  # type: ignore[arg-type]
                    BytesIO(),
                    encoding=encoding,
                    errors=errors,
                    newline=newline,
                    write_through=True,
                )
            )

    async def aclose(self) -> None:
        if not self._rolled:
            self._fp.close()
            return

        await super().aclose()

    async def _check(self) -> None:
        if self._rolled or self._fp.tell() < self._max_size:
            return

        await self.rollover()

    async def rollover(self) -> None:
        if self._rolled:
            return

        self._rolled = True
        buffer = self._fp
        buffer.seek(0)
        self._fp = await to_thread.run_sync(

        )
        await self.write(buffer.read())
        buffer.close()

    @property
    def closed(self) -> bool:
        return self._fp.closed

    async def read(self, size: int = -1) -> AnyStr:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.read(size)

        return await super().read(size)  # type: ignore[return-value]

        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.read1(size)

        return await super().read1(size)

    async def readline(self) -> AnyStr:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.readline()

        return await super().readline()  # type: ignore[return-value]

    async def readlines(self) -> list[AnyStr]:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.readlines()

        return await super().readlines()  # type: ignore[return-value]

        if not self._rolled:
            await checkpoint_if_cancelled()
            self._fp.readinto(b)

        return await super().readinto(b)

        if not self._rolled:
            await checkpoint_if_cancelled()
            self._fp.readinto(b)

        return await super().readinto1(b)

    async def seek(self, offset: int, whence: int | None = os.SEEK_SET) -> int:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.seek(offset, whence)

        return await super().seek(offset, whence)

    async def tell(self) -> int:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.tell()

        return await super().tell()

    async def truncate(self, size: int | None = None) -> int:
        if not self._rolled:
            await checkpoint_if_cancelled()
            return self._fp.truncate(size)

        return await super().truncate(size)

    @overload

    @overload

    async def write(self, b: ReadableBuffer | str) -> int:
        """

        If the file has not yet been rolled over, the data is written synchronously,
        and a rollover is triggered if the size exceeds the maximum size.

        :param s: The data to write.
        :return: The number of bytes written.
        :raises RuntimeError: If the underlying file is not initialized.

        """
        if not self._rolled:
            await checkpoint_if_cancelled()
            result = self._fp.write(b)
            await self._check()
            return result

        return await super().write(b)  # type: ignore[misc]

    @overload
    async def writelines(

    ) -> None: ...
    @overload
    async def writelines(

    ) -> None: ...

    async def writelines(self, lines: Iterable[str] | Iterable[ReadableBuffer]) -> None:
        """

        If the file has not yet been rolled over, the lines are written synchronously,
        and a rollover is triggered if the size exceeds the maximum size.

        :param lines: An iterable of lines to write.
        :raises RuntimeError: If the underlying file is not initialized.

        """
        if not self._rolled:
            await checkpoint_if_cancelled()
            result = self._fp.writelines(lines)
            await self._check()
            return result

        return await super().writelines(lines)  # type: ignore[misc]

    """

    perform directory creation and cleanup operations in a background thread.

    :param ignore_cleanup_errors: Whether to ignore errors during cleanup
        (Python 3.10+).
    :param delete: Whether to delete the directory upon closing (Python 3.12+).
    """

    def __init__(:
        self,
        suffix: AnyStr | None = None,
        prefix: AnyStr | None = None,
        dir: AnyStr | None = None,
        *,
        ignore_cleanup_errors: bool = False,
        delete: bool = True,
    ) -> None:
        self.suffix: AnyStr | None = suffix
        self.prefix: AnyStr | None = prefix
        self.dir: AnyStr | None = dir
        self.ignore_cleanup_errors = ignore_cleanup_errors
        self.delete = delete

    async def __aenter__(self) -> str:
        params: dict[str, Any] = {
            "suffix": self.suffix,
            "prefix": self.prefix,
            "dir": self.dir,
        }
        if sys.version_info >= (3, 10):
            params["ignore_cleanup_errors"] = self.ignore_cleanup_errors

        if sys.version_info >= (3, 12):
            params["delete"] = self.delete

        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:

            await to_thread.run_sync(

            )

    async def cleanup(self) -> None:

@overload

    suffix: str | None = None,
    prefix: str | None = None,
    dir: str | None = None,
    text: bool = False,
) -> tuple[int, str]: ...

@overload

    suffix: bytes | None = None,
    prefix: bytes | None = None,
    dir: bytes | None = None,
    text: bool = False,
) -> tuple[int, bytes]: ...

    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: AnyStr | None = None,
    text: bool = False,
) -> tuple[int, str | bytes]:
    """

    name.

    :param suffix: Suffix to be added to the file name.
    :param prefix: Prefix to be added to the file name.

    :param text: Whether the file is opened in text mode.
    :return: A tuple containing the file descriptor and the file name.

    """

@overload

    suffix: str | None = None,
    prefix: str | None = None,
    dir: str | None = None,
) -> str: ...

@overload

    suffix: bytes | None = None,
    prefix: bytes | None = None,
    dir: bytes | None = None,
) -> bytes: ...

    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: AnyStr | None = None,
) -> str | bytes:
    """

    :param suffix: Suffix to be added to the directory name.
    :param prefix: Prefix to be added to the directory name.

    """

    """

    """

    """

    """

