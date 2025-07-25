import subprocess
import sys
from textwrap import dedent

import pytest

def test_excepthook(tmpdir):
    app = tmpdir.join("app.py")
    app.write(
        dedent(
            """
    from posthog import Posthog

    # frame_value = "LOL"

    1/0
    """
        )
    )

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.check_output([sys.executable, str(app)], stderr=subprocess.STDOUT)

    output = excinfo.value.output

    assert b"ZeroDivisionError" in output
    assert b"LOL" in output

    assert (
        b'"$exception_list": [{"mechanism": {"type": "generic", "handled": true}, "module": null, "type": "ZeroDivisionError", "value": "division by zero", "stacktrace": {"frames": [{"platform": "python", "filename": "app.py", "abs_path"'
        in output
    )

def test_trying_to_use_django_integration(tmpdir):
    app = tmpdir.join("app.py")
    app.write(
        dedent(
            """
    from posthog import Posthog, Integrations

    # frame_value = "LOL"

    1/0
    """
        )
    )

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.check_output([sys.executable, str(app)], stderr=subprocess.STDOUT)

    output = excinfo.value.output

    assert b"ZeroDivisionError" in output
    assert b"LOL" in output

    assert (
        b'"$exception_list": [{"mechanism": {"type": "generic", "handled": true}, "module": null, "type": "ZeroDivisionError", "value": "division by zero", "stacktrace": {"frames": [{"platform": "python", "filename": "app.py", "abs_path"'
        in output
    )
