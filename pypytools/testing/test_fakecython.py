import sys
from pypytools._fakecython import FakeCython

class TestFakeCython:

    def test_fakecython(self):
        fake = FakeCython()
        @fake.cfunc
        @fake.locals(a=int, b=int)
        @fake.returns(int)
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
