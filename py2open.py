#!/usr/bin/env python
"""
Workaround lack of encoding in py2:open  
# https://stackoverflow.com/questions/10971033/backporting-python-3-openencoding-utf-8-to-python-2
"""
import sys

if sys.version_info[0] > 2:   # py3
    pass
else:  # py2
    import codecs
    import warnings
    def open(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if newline is not None:
            warnings.warn('newline is not supported in py2')
        if not closefd:
            warnings.warn('closefd is not supported in py2')
        if opener is not None:
            warnings.warn('opener is not supported in py2')
        pass
        return codecs.open(filename=path, mode=mode, encoding=encoding, errors=errors, buffering=buffering)
    pass
pass


