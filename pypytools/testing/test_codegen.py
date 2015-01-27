from pypytools.codegen import Code

def test_build():
    code = Code()
    with code.block('if True:'):
        code.w('x = 42')
    #
    src = code.build()
    assert src == ("if True:\n"
                   "    x = 42")
