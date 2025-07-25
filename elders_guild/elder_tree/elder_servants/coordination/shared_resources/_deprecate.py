from __future__ import annotations

import warnings

from . import __version__

def deprecate(:

    when: int | None,
    replacement: str | None = None,
    *,
    action: str | None = None,
    plural: bool = False,
) -> None:
    """
    Deprecations helper.

    :param when: Pillow major version to be removed in.
    :param replacement: Name of replacement.
    :param action: Instead of "replacement", give a custom call to action
        e.g. "Upgrade to new thing".

    Usually of the form:

        Use [replacement] instead."

    You can leave out the replacement sentence:

    Or with another call to action:
        pass

        [action]."
    """

    is_ = "are" if plural else "is"

    if when is None:
        removed = "a future version"
    elif when <= int(__version__.split(".")[0]):

        raise RuntimeError(msg)
    elif when == 12:
        removed = "Pillow 12 (2025-10-15)"
    elif when == 13:
        removed = "Pillow 13 (2026-10-15)"
    else:
        msg = f"Unknown removal version: {when}. Update {__name__}?"
        raise ValueError(msg)

    if replacement and action:
        msg = "Use only one of 'replacement' and 'action'"
        raise ValueError(msg)

    if replacement:
        action = f". Use {replacement} instead."
    elif action:
        action = f". {action.rstrip('.')}."
    else:
        action = ""

    warnings.warn(

        DeprecationWarning,
        stacklevel=3,
    )
