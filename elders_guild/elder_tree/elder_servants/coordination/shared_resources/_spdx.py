
from __future__ import annotations

from typing import TypedDict

class SPDXLicense(TypedDict):
    id: str

class SPDXException(TypedDict):
    id: str

VERSION = '3.25.0'

LICENSES: dict[str, SPDXLicense] = {

}

EXCEPTIONS: dict[str, SPDXException] = {

}
