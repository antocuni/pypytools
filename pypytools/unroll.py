import py
import types
import ast

def d(node):
    import astpp
    import codegen
    print astpp.dump(node)
    print
    print codegen.to_source(node)

class Closure(object):

    def __init__(self, fn, **extravars):
        self.fn = fn
        self.extravars = extravars
        #
        for freevar, cell in zip(fn.__code__.co_freevars, fn.__closure__):
            self.extravars[freevar] = cell.cell_contents
        #
        makesrc = self._create_src()
        self.tree = ast.parse(makesrc)

    def _create_src(self):
        freevars = self.extravars.keys()
        innersrc = py.code.Source(self.fn)
        lines = [
            'def make(%s):' % ', '.join(freevars),
            str(innersrc.indent()),
            '    return %s' % self.fn.__name__
            ]
        return '\n'.join(lines)

    def make(self):
        tree = ast.fix_missing_locations(self.tree)
        d = {}
        co = compile(tree, self.fn.__code__.co_filename, 'exec')
        exec co in d
        make = d['make']
        return make(**self.extravars)


def fake_unroll(**kwargs):
    def identity(fn):
        return fn
    return identity


class unroll(object):

    def __init__(self, **extravars):
        self.extravars = extravars
        # we need to specify a fake unroll, to ignore the existing @unroll
        # decorator in the fn source code
        self.extravars['unroll'] = fake_unroll

    def __call__(self, fn):
        closure = Closure(fn, **self.extravars)
        return closure.make()
