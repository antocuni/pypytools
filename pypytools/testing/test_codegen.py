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

def test_args():
    varnames = ['x', 'y']
    assert Code.args(varnames) == 'x, y'
    assert Code.args(varnames, '*args') == 'x, y, *args'
    assert Code.args(varnames, '*args', '**kwargs') == 'x, y, *args, **kwargs'

def test_def_():
    code = Code()
    with code.def_('foo', ['x', 'y']):
        code.w('return x+y')
    #
    code.compile()
    foo = code['foo']
    assert foo(1, 2) == 3

def test_call():
    assert Code.call('foo', ['x', 'y']) == 'foo(x, y)'

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

