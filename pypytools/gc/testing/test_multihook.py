import pytest
from pypytools import IS_PYPY
from pypytools.gc.multihook import MultiHook, GcHooks
from pypytools.gc.testing.test_fakegc import fakegc

@pytest.fixture
def mh(monkeypatch):
    # install itself as MultiHook singleton, to avoid leaving around
    # global state
    obj = MultiHook()
    monkeypatch.setattr(MultiHook, '_instance', obj)
    return obj

class GcStatistics(GcHooks):
    def __init__(self):
        self.reset()

    def reset(self):
        self.minors = []
        self.steps = []
        self.collects = []

    def on_gc_minor(self, stats):
        self.minors.append(stats)

    def on_gc_collect_step(self, stats):
        self.steps.append(stats)

    def on_gc_collect(self, stats):
        self.collects.append(stats)



class TestMultiHook:

    def test_add_remove_hook(self, fakegc):
        class A:
            on_gc_minor = 'A minor'
            on_gc_collect_step = 'A step'
            on_gc_collect = 'A collect'

        class B:
            on_gc_minor = 'B minor'

        mh = MultiHook()
        a = A()
        b = B()
        mh.add(a)
        assert mh.minor_callbacks == ['A minor']
        assert mh.collect_step_callbacks == ['A step']
        assert mh.collect_callbacks == ['A collect']

        mh.add(b)
        assert mh.minor_callbacks == ['A minor', 'B minor']
        assert mh.collect_step_callbacks == ['A step']
        assert mh.collect_callbacks == ['A collect']

        mh.remove(a)
        assert mh.minor_callbacks == ['B minor']
        assert mh.collect_step_callbacks == []
        assert mh.collect_callbacks == []

    def test_install_hook(self, fakegc):
        a = GcStatistics()
        mh = MultiHook()
        mh.add(a)

        fakegc.fire_minor('minor')
        fakegc.fire_step('step')
        fakegc.fire_collect('collect')
        assert a.minors == ['minor']
        assert a.steps == ['step']
        assert a.collects == ['collect']

    def test_dont_install_hook_if_no_cb(self, fakegc):
        class A(object):
            def __init__(self):
                self.minors = []

            def on_gc_minor(self, stats):
                self.minors.append(stats)

        a = A()
        mh = MultiHook()
        mh.add(a)
        assert fakegc.hooks.on_gc_minor is not None
        assert fakegc.hooks.on_gc_collect_step is None
        assert fakegc.hooks.on_gc_collect is None
        fakegc.fire_minor('minor')
        assert a.minors == ['minor']

    def test_check_no_other_hooks(self, fakegc):
        # check that nobody else is messing with gc.hooks directly
        fakegc.hooks.on_gc_minor = lambda stats: None
        with pytest.raises(ValueError):
            MultiHook()

    def test_check_no_other_hooks_when_adding(self, fakegc):
        # check that nobody else is messing with gc.hooks directly
        mh = MultiHook()
        fakegc.hooks.on_gc_minor = lambda stats: None
        with pytest.raises(ValueError):
            mh.add(object())


class TestGcHooks(object):

    def test_mh(self, fakegc, mh):
        assert MultiHook.get() is mh

    def test_enable_disable(self, fakegc, mh):
        class A(GcHooks):
            def __init__(self):
                self.minors = []

            def on_gc_minor(self, stats):
                self.minors.append(stats)

        a1 = A()
        a2 = A()
        a1.enable()
        fakegc.fire_minor(1)
        a2.enable()
        fakegc.fire_minor(2)
        a1.disable()
        fakegc.fire_minor(3)

        assert a1.minors == [1, 2]
        assert a2.minors == [2, 3]

    def test_real_hooks(self, mh):
        # note that:
        #   1. we are NOT using fakegc, so MultiHook uses the builtin real gc mod
        #   2. we run this test also on CPython. The point is that it should
        #      still run without failing
        import gc
        a1 = GcStatistics()
        a2 = GcStatistics()
        a1.enable()
        a2.enable()
        gc.collect()
        if IS_PYPY:
            assert a1.collects[0].count >= 1
            assert a2.collects[0].count >= 1
