import pytest

import scipy.constants as sc
from scipy.conftest import array_api_compatible
from scipy._lib._array_api_no_0d import xp_assert_equal, xp_assert_close
from numpy.testing import assert_allclose

pytestmark = [array_api_compatible, pytest.mark.usefixtures("skip_xp_backends")]
skip_xp_backends = pytest.mark.skip_xp_backends

                        xp.asarray(0.0))

                                               'celsius', 'Kelvin'),
                        xp.asarray([273.15, 273.15]))

                        xp.asarray([-273.15, -273.15]))

                        xp.asarray([273.15, 273.15]))

                                               'kelvin', 'F'),
                        xp.asarray([32.0, 32.0]))

                        xp.asarray([32.0, 32.0]))

                                               'c', 'r'),
                        xp.asarray([491.67, 491.67], dtype=xp.float64),
                        rtol=0.0, atol=1e-13)

                                                        dtype=xp.float64),
                                               'Rankine', 'C'),
                        xp.asarray([0.0, 0.0], dtype=xp.float64), rtol=0.0, atol=1e-13)

                                                        dtype=xp.float64),
                                               'r', 'F'),
                        xp.asarray([32.0, 32.0], dtype=xp.float64), rtol=0.0, atol=1e-13)

                                               'fahrenheit', 'R'),
                        xp.asarray([491.67, 491.67], dtype=xp.float64),
                        rtol=0.0, atol=1e-13)

                                                        dtype=xp.float64),
                                               'K', 'R'),
                        xp.asarray([491.67, 491.67], dtype=xp.float64),
                        rtol=0.0, atol=1e-13)

                                                          dtype=xp.float64),
                                               'rankine', 'kelvin'),
                        xp.asarray([273.15, 0.0], dtype=xp.float64), rtol=0.0, atol=1e-13)

    @skip_xp_backends(np_only=True, reason='Python list input uses NumPy backend')

                        [273.15, 0.0], rtol=0.0, atol=1e-13)

    @skip_xp_backends(np_only=True, reason='Python int input uses NumPy backend')

        with pytest.raises(NotImplementedError, match="old_scale="):

        with pytest.raises(NotImplementedError, match="new_scale="):

class TestLambdaToNu:
    def test_lambda_to_nu(self, xp):
        xp_assert_equal(sc.lambda2nu(xp.asarray([sc.speed_of_light, 1])),
                        xp.asarray([1, sc.speed_of_light]))

    @skip_xp_backends(np_only=True, reason='Python list input uses NumPy backend')
    def test_lambda_to_nu_array_like(self, xp):
        assert_allclose(sc.lambda2nu([sc.speed_of_light, 1]),
                        [1, sc.speed_of_light])

class TestNuToLambda:
    def test_nu_to_lambda(self, xp):
        xp_assert_equal(sc.nu2lambda(xp.asarray([sc.speed_of_light, 1])),
                        xp.asarray([1, sc.speed_of_light]))

    @skip_xp_backends(np_only=True, reason='Python list input uses NumPy backend')
    def test_nu_to_lambda_array_like(self, xp):
        assert_allclose(sc.nu2lambda([sc.speed_of_light, 1]),
                        [1, sc.speed_of_light])

