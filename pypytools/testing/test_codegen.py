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
