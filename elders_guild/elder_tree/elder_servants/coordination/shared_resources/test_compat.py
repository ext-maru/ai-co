from os.path import join
from io import BufferedReader, BytesIO

from numpy.compat import isfileobj
from numpy.testing import assert_

def test_isfileobj():

        filename = join(folder, 'a.bin')

        with open(filename, 'wb') as f:
            assert_(isfileobj(f))

        with open(filename, 'ab') as f:
            assert_(isfileobj(f))

        with open(filename, 'rb') as f:
            assert_(isfileobj(f))

        assert_(isfileobj(BufferedReader(BytesIO())) is False)
