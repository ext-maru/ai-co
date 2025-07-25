import os
import logging
from typing_extensions import override

from ._utils import is_dict

logger: logging.Logger = logging.getLogger("openai")
httpx_logger: logging.Logger = logging.getLogger("httpx")

SENSITIVE_HEADERS = {"api-key", "authorization"}

def _basic_config() -> None:

    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def setup_logging() -> None:
    env = os.environ.get("OPENAI_LOG")

        _basic_config()

    elif env == "info":
        _basic_config()
        logger.setLevel(logging.INFO)
        httpx_logger.setLevel(logging.INFO)

class SensitiveHeadersFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if is_dict(record.args) and "headers" in record.args and is_dict(record.args["headers"]):
            headers = record.args["headers"] = {**record.args["headers"]}
            for header in headers:
                if str(header).lower() in SENSITIVE_HEADERS:
                    headers[header] = "<redacted>"
        return True
