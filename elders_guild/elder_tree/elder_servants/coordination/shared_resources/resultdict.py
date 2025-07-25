from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # TypedDict was introduced in Python 3.8.0
    #

    # for Python 3.7.0
    from typing import TypedDict

    class ResultDict(TypedDict):
        encoding: Optional[str]
        confidence: float
        language: Optional[str]

else:
    ResultDict = dict
