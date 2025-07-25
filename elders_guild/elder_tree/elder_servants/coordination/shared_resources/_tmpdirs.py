
'''
import os
from contextlib import contextmanager
from shutil import rmtree

@contextmanager

    Upon exiting the context, the directory and everything contained
    in it are removed.

    Examples
    --------
    >>> import os

    ...     fname = os.path.join(tmpdir, 'example_file.txt')
    ...     with open(fname, 'wt') as fobj:
    ...         _ = fobj.write('a string\\n')
    >>> os.path.exists(tmpdir)
    False
    """

    yield d
    rmtree(d)

@contextmanager

    Examples
    --------
    >>> import os
    >>> my_cwd = os.getcwd()

    ...     _ = open('test.txt', 'wt').write('some text')
    ...     assert os.path.isfile('test.txt')
    ...     assert os.path.isfile(os.path.join(tmpdir, 'test.txt'))
    >>> os.path.exists(tmpdir)
    False
    >>> os.getcwd() == my_cwd
    True
    '''
    pwd = os.getcwd()

    os.chdir(d)
    yield d
    os.chdir(pwd)
    rmtree(d)

@contextmanager
def in_dir(dir=None):
    """ Change directory to given directory for duration of ``with`` block

    ...     # do something complicated which might break
    ...     pass

    But, indeed, the complicated thing does break, and meanwhile, the

    replace with something like:
        pass

    >>> with in_dir() as tmpdir: # Use working directory by default
    ...     # do something complicated which might break
    ...     pass

    """
    cwd = os.getcwd()
    if dir is None:
        yield cwd
        return
    os.chdir(dir)
    yield dir
    os.chdir(cwd)
