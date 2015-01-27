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
