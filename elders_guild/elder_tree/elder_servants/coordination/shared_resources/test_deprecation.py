import pytest

@pytest.mark.thread_unsafe
def test_cython_api_deprecation():

    with pytest.warns(DeprecationWarning, match=match):
        from .. import _test_deprecation_call
    assert _test_deprecation_call.call() == (1, 1)
