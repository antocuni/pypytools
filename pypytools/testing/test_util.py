from pypytools.util import clonefunc

def test_clonefunc():
    def foo(a, b):
        return a+b

    foo2 = clonefunc(foo)
    assert foo is not foo2
    assert foo.__code__ is not foo2.__code__
    assert foo.__code__.co_code is foo2.__code__.co_code
    assert foo2.__name__ == 'foo'
    assert foo2(40, 2) == 42
