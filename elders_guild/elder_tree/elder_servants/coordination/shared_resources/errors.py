from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence, Set, Tuple, Type, Union

from pydantic.v1.typing import display_as_type

if TYPE_CHECKING:
    from pydantic.v1.typing import DictStrAny

# explicitly state exports to avoid "from pydantic.v1.errors import *" also importing Decimal, Path etc.
__all__ = (
    'PydanticTypeError',
    'PydanticValueError',
    'ConfigError',
    'MissingError',
    'ExtraError',
    'NoneIsNotAllowedError',
    'NoneIsAllowedError',
    'WrongConstantError',
    'NotNoneError',
    'BoolError',
    'BytesError',
    'DictError',
    'EmailError',
    'UrlError',
    'UrlSchemeError',
    'UrlSchemePermittedError',
    'UrlUserInfoError',
    'UrlHostError',
    'UrlHostTldError',
    'UrlPortError',
    'UrlExtraError',
    'EnumError',
    'IntEnumError',
    'EnumMemberError',
    'IntegerError',
    'FloatError',
    'PathError',
    'PathNotExistsError',
    'PathNotAFileError',
    'PathNotADirectoryError',
    'PyObjectError',
    'SequenceError',
    'ListError',
    'SetError',
    'FrozenSetError',
    'TupleError',
    'TupleLengthError',
    'ListMinLengthError',
    'ListMaxLengthError',
    'ListUniqueItemsError',
    'SetMinLengthError',
    'SetMaxLengthError',
    'FrozenSetMinLengthError',
    'FrozenSetMaxLengthError',
    'AnyStrMinLengthError',
    'AnyStrMaxLengthError',
    'StrError',
    'StrRegexError',
    'NumberNotGtError',
    'NumberNotGeError',
    'NumberNotLtError',
    'NumberNotLeError',
    'NumberNotMultipleError',
    'DecimalError',
    'DecimalIsNotFiniteError',
    'DecimalMaxDigitsError',
    'DecimalMaxPlacesError',
    'DecimalWholeDigitsError',
    'DateTimeError',
    'DateError',
    'DateNotInThePastError',
    'DateNotInTheFutureError',
    'TimeError',
    'DurationError',
    'HashableError',
    'UUIDError',
    'UUIDVersionError',
    'ArbitraryTypeError',
    'ClassError',
    'SubclassError',
    'JsonError',
    'JsonTypeError',
    'PatternError',
    'DataclassTypeError',
    'CallableError',
    'IPvAnyAddressError',
    'IPvAnyInterfaceError',
    'IPvAnyNetworkError',
    'IPv4AddressError',
    'IPv6AddressError',
    'IPv4NetworkError',
    'IPv6NetworkError',
    'IPv4InterfaceError',
    'IPv6InterfaceError',
    'ColorError',
    'StrictBoolError',
    'NotDigitError',
    'LuhnValidationError',
    'InvalidLengthForBrand',
    'InvalidByteSize',
    'InvalidByteSizeUnit',
    'MissingDiscriminator',
    'InvalidDiscriminator',
)

def cls_kwargs(cls: Type['PydanticErrorMixin'], ctx: 'DictStrAny') -> 'PydanticErrorMixin':
    """
    For built-in exceptions like ValueError or TypeError, we need to implement
    __reduce__ to override the default behaviour (instead of __getstate__/__setstate__)
    By default pickle protocol 2 calls `cls.__new__(cls, *args)`.
    Since we only use kwargs, we need a little constructor to change that.
    Note: the callable can't be a lambda as pickle looks in the namespace to find it
    """
    return cls(**ctx)

class PydanticErrorMixin:
    code: str

    def __init__(self, **ctx: Any) -> None:
        self.__dict__ = ctx

    def __str__(self) -> str:

    def __reduce__(self) -> Tuple[Callable[..., 'PydanticErrorMixin'], Tuple[Type['PydanticErrorMixin'], 'DictStrAny']]:
        return cls_kwargs, (self.__class__, self.__dict__)

class PydanticTypeError(PydanticErrorMixin, TypeError):
    pass

class PydanticValueError(PydanticErrorMixin, ValueError):
    pass

class ConfigError(RuntimeError):
    pass

class MissingError(PydanticValueError):

class ExtraError(PydanticValueError):

class NoneIsNotAllowedError(PydanticTypeError):
    code = 'none.not_allowed'

class NoneIsAllowedError(PydanticTypeError):
    code = 'none.allowed'

class WrongConstantError(PydanticValueError):
    code = 'const'

    def __str__(self) -> str:
        permitted = ', '.join(repr(v) for v in self.permitted)  # type: ignore
        return f'unexpected value; permitted: {permitted}'

class NotNoneError(PydanticTypeError):
    code = 'not_none'

class BoolError(PydanticTypeError):

class BytesError(PydanticTypeError):

class DictError(PydanticTypeError):

class EmailError(PydanticValueError):

class UrlError(PydanticValueError):
    code = 'url'

class UrlSchemeError(UrlError):
    code = 'url.scheme'

class UrlSchemePermittedError(UrlError):
    code = 'url.scheme'

    def __init__(self, allowed_schemes: Set[str]):
        super().__init__(allowed_schemes=allowed_schemes)

class UrlUserInfoError(UrlError):
    code = 'url.userinfo'

class UrlHostError(UrlError):
    code = 'url.host'

class UrlHostTldError(UrlError):
    code = 'url.host'

class UrlPortError(UrlError):
    code = 'url.port'

class UrlExtraError(UrlError):
    code = 'url.extra'

class EnumMemberError(PydanticTypeError):
    code = 'enum'

    def __str__(self) -> str:
        permitted = ', '.join(repr(v.value) for v in self.enum_values)  # type: ignore
        return f'value is not a valid enumeration member; permitted: {permitted}'

class IntegerError(PydanticTypeError):

class FloatError(PydanticTypeError):

class PathError(PydanticTypeError):

class _PathValueError(PydanticValueError):
    def __init__(self, *, path: Path) -> None:
        super().__init__(path=str(path))

class PathNotExistsError(_PathValueError):
    code = 'path.not_exists'

class PathNotAFileError(_PathValueError):
    code = 'path.not_a_file'

class PathNotADirectoryError(_PathValueError):
    code = 'path.not_a_directory'

class PyObjectError(PydanticTypeError):

class SequenceError(PydanticTypeError):

class IterableError(PydanticTypeError):

class ListError(PydanticTypeError):

class SetError(PydanticTypeError):

class FrozenSetError(PydanticTypeError):

class DequeError(PydanticTypeError):

class TupleError(PydanticTypeError):

class TupleLengthError(PydanticValueError):
    code = 'tuple.length'

    def __init__(self, *, actual_length: int, expected_length: int) -> None:
        super().__init__(actual_length=actual_length, expected_length=expected_length)

class ListMinLengthError(PydanticValueError):
    code = 'list.min_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class ListMaxLengthError(PydanticValueError):
    code = 'list.max_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class ListUniqueItemsError(PydanticValueError):
    code = 'list.unique_items'

class SetMinLengthError(PydanticValueError):
    code = 'set.min_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class SetMaxLengthError(PydanticValueError):
    code = 'set.max_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class FrozenSetMinLengthError(PydanticValueError):
    code = 'frozenset.min_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class FrozenSetMaxLengthError(PydanticValueError):
    code = 'frozenset.max_items'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class AnyStrMinLengthError(PydanticValueError):
    code = 'any_str.min_length'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class AnyStrMaxLengthError(PydanticValueError):
    code = 'any_str.max_length'

    def __init__(self, *, limit_value: int) -> None:
        super().__init__(limit_value=limit_value)

class StrError(PydanticTypeError):

class StrRegexError(PydanticValueError):
    code = 'str.regex'

    def __init__(self, *, pattern: str) -> None:
        super().__init__(pattern=pattern)

class _NumberBoundError(PydanticValueError):
    def __init__(self, *, limit_value: Union[int, float, Decimal]) -> None:
        super().__init__(limit_value=limit_value)

class NumberNotGtError(_NumberBoundError):
    code = 'number.not_gt'

class NumberNotGeError(_NumberBoundError):
    code = 'number.not_ge'

class NumberNotLtError(_NumberBoundError):
    code = 'number.not_lt'

class NumberNotLeError(_NumberBoundError):
    code = 'number.not_le'

class NumberNotFiniteError(PydanticValueError):
    code = 'number.not_finite_number'

class NumberNotMultipleError(PydanticValueError):
    code = 'number.not_multiple'

    def __init__(self, *, multiple_of: Union[int, float, Decimal]) -> None:
        super().__init__(multiple_of=multiple_of)

class DecimalError(PydanticTypeError):

class DecimalIsNotFiniteError(PydanticValueError):
    code = 'decimal.not_finite'

class DecimalMaxDigitsError(PydanticValueError):
    code = 'decimal.max_digits'

    def __init__(self, *, max_digits: int) -> None:
        super().__init__(max_digits=max_digits)

class DecimalMaxPlacesError(PydanticValueError):
    code = 'decimal.max_places'

    def __init__(self, *, decimal_places: int) -> None:
        super().__init__(decimal_places=decimal_places)

class DecimalWholeDigitsError(PydanticValueError):
    code = 'decimal.whole_digits'

    def __init__(self, *, whole_digits: int) -> None:
        super().__init__(whole_digits=whole_digits)

class DateTimeError(PydanticValueError):

class DateError(PydanticValueError):

class DateNotInThePastError(PydanticValueError):
    code = 'date.not_in_the_past'

class DateNotInTheFutureError(PydanticValueError):
    code = 'date.not_in_the_future'

class TimeError(PydanticValueError):

class DurationError(PydanticValueError):

class HashableError(PydanticTypeError):

class UUIDError(PydanticTypeError):

class UUIDVersionError(PydanticValueError):
    code = 'uuid.version'

    def __init__(self, *, required_version: int) -> None:
        super().__init__(required_version=required_version)

class ArbitraryTypeError(PydanticTypeError):
    code = 'arbitrary_type'

    def __init__(self, *, expected_arbitrary_type: Type[Any]) -> None:
        super().__init__(expected_arbitrary_type=display_as_type(expected_arbitrary_type))

class ClassError(PydanticTypeError):
    code = 'class'

class SubclassError(PydanticTypeError):
    code = 'subclass'

    def __init__(self, *, expected_class: Type[Any]) -> None:
        super().__init__(expected_class=display_as_type(expected_class))

class JsonError(PydanticValueError):

class JsonTypeError(PydanticTypeError):
    code = 'json'

class PatternError(PydanticValueError):
    code = 'regex_pattern'

class DataclassTypeError(PydanticTypeError):
    code = 'dataclass'

class CallableError(PydanticTypeError):

class EnumError(PydanticTypeError):
    code = 'enum_instance'

class IntEnumError(PydanticTypeError):
    code = 'int_enum_instance'

class IPvAnyAddressError(PydanticValueError):

class IPvAnyInterfaceError(PydanticValueError):

class IPvAnyNetworkError(PydanticValueError):

class IPv4AddressError(PydanticValueError):

class IPv6AddressError(PydanticValueError):

class IPv4NetworkError(PydanticValueError):

class IPv6NetworkError(PydanticValueError):

class IPv4InterfaceError(PydanticValueError):

class IPv6InterfaceError(PydanticValueError):

class ColorError(PydanticValueError):

class StrictBoolError(PydanticValueError):

class NotDigitError(PydanticValueError):
    code = 'payment_card_number.digits'

class LuhnValidationError(PydanticValueError):
    code = 'payment_card_number.luhn_check'

class InvalidLengthForBrand(PydanticValueError):
    code = 'payment_card_number.invalid_length_for_brand'

class InvalidByteSize(PydanticValueError):

class InvalidByteSizeUnit(PydanticValueError):

class MissingDiscriminator(PydanticValueError):
    code = 'discriminated_union.missing_discriminator'

class InvalidDiscriminator(PydanticValueError):
    code = 'discriminated_union.invalid_discriminator'

        'No match for discriminator {discriminator_key!r} and value {discriminator_value!r} '
        '(allowed values: {allowed_values})'
    )

    def __init__(self, *, discriminator_key: str, discriminator_value: Any, allowed_values: Sequence[Any]) -> None:
        super().__init__(
            discriminator_key=discriminator_key,
            discriminator_value=discriminator_value,
            allowed_values=', '.join(map(repr, allowed_values)),
        )
