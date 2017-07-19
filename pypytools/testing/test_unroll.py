import sys
import inspect
import dis
from pypytools.unroll import unroll, Closure
from pypytools.util import PY3

if PY3:
    from io import StringIO
else:
    from cStringIO import StringIO


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

def test_existing_closure():
    y = 10
    @unroll(x=52)
    def foo():
        return x-y
    assert foo() == 42


def test_existing_closure_override():
    x = 10
    @unroll(x=42)
    def foo():
        return x
    assert foo() == 42


def test_getsource():
    def foo():
        pass
    #
    foo2 = unroll()(foo)
    src = inspect.getsource(foo)
    src2 = inspect.getsource(foo2)
    assert src == src2


def test_unrolling(monkeypatch):
    @unroll(items=(1, 2, 3))
    def foo():
        x = 0
        for i in items:
            x += i
        return x
    assert foo() == 6
    #
    stdout = StringIO()
    monkeypatch.setattr(sys, 'stdout', stdout)
    dis.dis(foo)
    monkeypatch.undo()
    assert 'FOR_ITER' not in stdout.getvalue()

def test_iterable(monkeypatch):
    items = iter([1, 2, 3])
    @unroll(items=items)
    def foo():
        x = 0
        for i in items:
            x += i
        return x
    assert foo() == 6
    #
    stdout = StringIO()
    monkeypatch.setattr(sys, 'stdout', stdout)
    dis.dis(foo)
    monkeypatch.undo()
    assert 'FOR_ITER' not in stdout.getvalue()


def my_global():
    return 42

def test_globals():
    @unroll()
    def foo():
        return my_global()
    assert foo() == 42

