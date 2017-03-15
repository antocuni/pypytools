from pypytools.codegen import Code

def test_build():
    code = Code()
    with code.block('if True:'):
        code.w('x = 42')
    #
    src = code.build()
    assert src == ("if True:\n"
                   "    x = 42")

def test_compile():
    code = Code()
    code.w('x = 42')
    code.compile()
    assert code['x'] == 42

def test_set_get_globals():
    code = Code()
    code['x'] = 42
    assert code['x'] == 42

def test_formatting():
    code = Code()
    code.w('{hello}')
    assert code.build() == '{hello}'
    #
    code = Code()
    code.w('{hello}', hello='world')
    assert code.build() == 'world'

def test_ww():
    code = Code()
    code.ww("""
        if {name}:
            return {name}
    """, name="x")
    src = code.build()
    assert src == ("if x:\n"
                   "    return x")


class TestArgsAndParams(object):
    
    def test_args_simple(self):
        code = Code()
        varnames = ['x', 'y']
        assert code.args(varnames) == 'x, y'
        assert code.args(varnames, '*args') == 'x, y, *args'
        assert code.args(varnames, '*args', '**kwargs') == 'x, y, *args, **kwargs'

    def test_params_simple(self):
        code = Code()
        varnames = ['x', 'y']
        assert code.params(varnames) == 'x, y'
        assert code.params(varnames, '*args') == 'x, y, *args'
        assert code.params(varnames, '*args', '**kwargs') == 'x, y, *args, **kwargs'

    def test_args_default(self):
        code = Code()
        varnames = ['x', ('y', 3)]
        assert code.args(varnames) == 'x, y=3'
        assert code.args(varnames, '*args') == 'x, y=3, *args'
        assert code.args(varnames, '*args', '**kwargs') == 'x, y=3, *args, **kwargs'

    def test_pyx_types(self):
        code = Code(pyx=True)
        varnames = ['x', 'y']
        assert code.args(varnames) == 'x, y'
        assert code.args(varnames, '*args') == 'x, y, *args'
        assert code.params(varnames) == 'object x, object y'
        assert code.params(varnames, '*args') == 'object x, object y, *args'

    def test_pyx_default(self):
        code = Code(pyx=True)
        varnames = ['x', ('y', 3)]
        assert code.params(varnames) == 'object x, object y=3'
        assert code.params(varnames, '*args') == 'object x, object y=3, *args'

    def test_call(self):
        for pyx in (False, True):
            code = Code(pyx=pyx)
            assert code.call('foo', ['x', 'y']) == 'foo(x, y)'


def test_def_():
    code = Code()
    with code.def_('foo', ['x', 'y']):
        code.w('return x+y')
    #
    code.compile()
    foo = code['foo']
    assert foo(1, 2) == 3

def test_def__default_args():
    code = Code()
    with code.def_('foo', ['x', ('y', 3)]):
        code.w('return x+y')
    #
    code.compile()
    foo = code['foo']
    assert foo(1) == 4
    assert foo(1, 10) == 11


def test_cpdef():
    code = Code()
    with code.cpdef_('foo', ['x', 'y']):
        code.w('return x+y')
    src = code.build()
    assert src == ("def foo(x, y):\n"
                   "    return x+y")
    #
    code = Code(pyx=True)
    with code.cpdef_('foo', ['x', 'y']):
        code.w('return x+y')
    src = code.build()
    assert src == ("cpdef foo(object x, object y):\n"
                   "    return x+y")


def test_cdef_var():
    code = Code()
    with code.def_('foo', ['x', 'y']):
        code.cdef_var('long', 'foo')
        code.cdef_var('int', 'bar', 42)
        code.w('return')
    src = code.build()
    assert src == ("def foo(x, y):\n"
                   "    return")
    #
    code = Code(pyx=True)
    with code.def_('foo', ['x', 'y']):
        code.cdef_var('long', 'foo')
        code.cdef_var('int', 'bar', 42)
        code.w('return')
    src = code.build()
    assert src == ("def foo(object x, object y):\n"
                   "    cdef long foo\n"
                   "    cdef int bar = 42\n"
                   "    return")



def test_global_kwargs():
    code = Code()
    code.global_scope.x = 42
    code.w('return {x}')
    assert code.build() == 'return 42'

def test_global_kwargs_override():
    code = Code()
    code.global_scope.x = 42
    code.w('return {x}', x=52)
    assert code.build() == 'return 52'

def test_block_autopass():
    code = Code()
    with code.block('if True:'):
        pass
    src = code.build()
    assert src == ("if True:\n"
                   "    pass")
    #
    code = Code()
    with code.block('if True:', autopass=False):
        pass
    src = code.build()
    assert src == "if True:"

def test_new_global():
    code = Code()
    name = code.new_global('x', 42)
    assert name == 'x'
    assert code['x'] == 42
    #
    name = code.new_global('x', 42)
    assert name == 'x'
    assert code['x'] == 42
    #
    name = code.new_global('x', 43)
    assert name == 'x__1'
    assert code['x'] == 42
    assert code['x__1'] == 43

class TestScope:
    
    def test_new_scope(self):
        code = Code()
        code.global_scope.x = 42
        code.global_scope.y = 52
        ns = code.new_scope(y=53, z=63)
        assert ns.__dict__ == dict(x=42, y=53, z=63)

    def test_scope_formatting(self):
        code = Code()
        ns = code.new_scope(y=52)
        ns.x = 42
        ns.w('x == {x}, y == {y}')
        assert code.build() == 'x == 42, y == 52'

    def test_block_namespace(self):
        code = Code()
        with code.block('if {name}:', name='x') as ns:
            ns.w('return {name}')
        #
        src = code.build()
        assert src == ("if x:\n"
                       "    return x")

