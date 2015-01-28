"""
CPython emulation of some of the __pypy__ builtins
"""

from pypytools import is_pypy

if is_pypy:
    from __pypy__ import newdict
    
else:

    def newdict(type):
        return {}
