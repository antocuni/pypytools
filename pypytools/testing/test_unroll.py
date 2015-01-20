from pypytools.unroll import unroll, Closure

def test_make_closure():
    def foo():
        return x

    cl = Closure(foo, x=42)
    foo2 = cl.make()
    assert foo2() == 42
    
    


def test_inject_value():
    @unroll(x=42)
    def foo():
        return x
    assert foo() == 42
