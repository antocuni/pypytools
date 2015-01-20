import py
import types
import ast

def d(node):
    import astpp
    import codegen
    print astpp.dump(node)
    print
    print codegen.to_source(node)

class unroll(object):

    def __init__(self, **extravars):
        self.extravars = extravars

    def __call__(self, fn):
        # we use py.code.Source because it automatically deindent the code, if
        # needed
        src = str(py.code.Source(fn))
        src = '#' + src # comment out the @unroll decorator, XXX
        node = ast.parse(src)
        #
        freevars = self.extravars.keys()
        funcdef = node.body[0]
        assert isinstance(funcdef, ast.FunctionDef)
        node.body[0] = inject_freevars(funcdef, freevars)
        ## node = Unroller(freevars).visit(node)
        node = ast.fix_missing_locations(node)
        #
        mydict = {}
        exec compile(node, fn.__module__, 'exec') in mydict
        make_fn = mydict['make_' + fn.__name__]
        new_fn = make_fn()
        new_fn = patch_closure(new_fn, self.extravars.values())
        return new_fn


def patch_closure(fn, freevals):
    def make_cell(value):
        # http://nedbatchelder.com/blog/201301/byterun_and_making_cells.html
        return (lambda x: lambda: x)(value).func_closure[0]

    cells = tuple([make_cell(val) for val in freevals])
    return types.FunctionType(fn.__code__, fn.__globals__, fn.__name__,
                              fn.__defaults__, cells)

    

def inject_freevars(funcdef, freevars):
    """
    functiondef is an ast node representing a function like this::
    
        def foo(a, b):
            ...

    it returns an ast node like this:

        def make_foo():
            x = None
            y = None
            def foo(a, b):
                ...
            return foo()
    """
    def make_assign(name):
        return ast.Assign(
            targets = [ast.Name(id=name, ctx=ast.Store())],
            value = ast.Name(id='None', ctx=ast.Load()))
    
    outerdef = ast.FunctionDef(
        name = 'make_'+funcdef.name,
        args = ast.arguments(args=[], vararg=None, kwarg=None, defaults=[]),
        decorator_list=[],
        body = [])

    outerdef.body =  [make_assign(name) for name in freevars]
    outerdef.body += [
        funcdef,
        ast.Return(value=ast.Name(id=funcdef.name, ctx=ast.Load())),
    ]
    return outerdef
