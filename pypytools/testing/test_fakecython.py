import sys
from pypytools._fakecython import FakeCython
from pypytools.util import PY3

if PY3:
    long = int

class TestFakeCython:

    def test_fakecython(self):
        fake = FakeCython()
        @fake.cfunc
        @fake.locals(a=long, b=long)
        @fake.returns(long)
        def foo(a, b):
            return a+b
        #
        assert foo(20, 22) == 42

    def test_context_manager(self):
        fakecython = FakeCython()
        sys.modules['cython'] = 'foobar'
        import cython
        assert cython == 'foobar'
        #
        with fakecython:
            import cython
            assert isinstance(cython, FakeCython)
        #
        import cython
        assert cython == 'foobar'
