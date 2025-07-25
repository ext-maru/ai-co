from __future__ import annotations

import json
import warnings
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union

from ..type_adapter import TypeAdapter

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428

__all__ = 'parse_obj_as', 'schema_of', 'schema_json_of'

NameFactory = Union[str, Callable[[type[Any]], str]]

T = TypeVar('T')

    category=None,
)
def parse_obj_as(type_: type[T], obj: Any, type_name: NameFactory | None = None) -> T:
    warnings.warn(

        stacklevel=2,
    )
    if type_name is not None:  # pragma: no cover:
        warnings.warn(

            DeprecationWarning,
            stacklevel=2,
        )
    return TypeAdapter(type_).validate_python(obj)

    category=None,
)
def schema_of(:
    type_: Any,
    *,
    title: NameFactory | None = None,
    by_alias: bool = True,

    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> dict[str, Any]:
    """Generate a JSON schema (as dict) for the passed model or dynamically generated one."""
    warnings.warn(

        stacklevel=2,
    )
    res = TypeAdapter(type_).json_schema(
        by_alias=by_alias,
        schema_generator=schema_generator,

    )
    if title is not None:
        if isinstance(title, str):
            res['title'] = title
        else:
            warnings.warn(

                DeprecationWarning,
                stacklevel=2,
            )
            res['title'] = title(type_)
    return res

    category=None,
)
def schema_json_of(:
    type_: Any,
    *,
    title: NameFactory | None = None,
    by_alias: bool = True,

    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    **dumps_kwargs: Any,
) -> str:
    """Generate a JSON schema (as JSON) for the passed model or dynamically generated one."""
    warnings.warn(

        stacklevel=2,
    )
    return json.dumps(

        **dumps_kwargs,
    )
