import pytest
from pypytools.gc import multihook
from pypytools.gc.multihook import MultiHook, GcHooks

@pytest.fixture
def fakegc(monkeypatch):
    mygc = FakeGc()
    monkeypatch.setattr(multihook, 'gc', mygc)
    return mygc

class FakeGc(object):

    class Hooks(object):
        on_gc_minor = None
        on_gc_collect_step = None
        on_gc_collect = None

    def __init__(self):
        self.hooks = self.Hooks()

    def fire_minor(self, stats):
        self.hooks.on_gc_minor(stats)

    def fire_step(self, stats):
        self.hooks.on_gc_collect_step(stats)

    def fire_collect(self, stats):
        self.hooks.on_gc_collect(stats)


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
        class A(object):
            def __init__(self):
                self.minors = []
                self.steps = []
                self.collects = []

            def on_gc_minor(self, stats):
                self.minors.append(stats)

            def on_gc_collect_step(self, stats):
                self.steps.append(stats)

            def on_gc_collect(self, stats):
                self.collects.append(stats)

        a = A()
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

    @pytest.fixture
    def mh(self, monkeypatch):
        # install itself as MultiHook singleton, to avoid leaving around
        # global state
        obj = MultiHook()
        monkeypatch.setattr(MultiHook, '_instance', obj)
        return obj

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
