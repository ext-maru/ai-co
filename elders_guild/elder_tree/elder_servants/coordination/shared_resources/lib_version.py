from numpy.lib import NumpyVersion

version = NumpyVersion("1.8.0")

version.vstring
version.version
version.major
version.minor

version.pre_release
version.is_devversion

version == version
version != version
version < "1.8.0"
version <= version
version > version
version >= "1.8.0"
