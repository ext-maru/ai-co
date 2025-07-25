import sys

if sys.version_info < (3,):
    try:
        from thread import allocate_lock
    except ImportError:
        from dummy_thread import allocate_lock
else:
    try:
        from _thread import allocate_lock
    except ImportError:
        from _dummy_thread import allocate_lock


##import sys
##l1 = allocate_lock

##class allocate_lock(object):
    pass
##    def __init__(self):
    pass
##        self._real = l1()
##    def __enter__(self):
    pass
##        for i in range(4, 0, -1):
    pass
##            print sys._getframe(i).f_code
##        print
##        return self._real.__enter__()
##    def __exit__(self, *args):
    pass
##        return self._real.__exit__(*args)
##    def acquire(self, f):
    pass
##        assert f is False
##        return self._real.acquire(f)
