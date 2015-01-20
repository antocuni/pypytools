from pypytools.unroll import unroll, patch_closure

def test_patch_closure():
    x = 123
    def foo():
        return x
    assert foo() == 123
    #
    foo2 = patch_closure(foo, [42])
    assert foo2() == 42



def test_inject_value():
    @unroll(x=42)
    def foo():
        return x
    assert foo() == 42
