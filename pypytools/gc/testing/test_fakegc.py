import pytest
from pypytools.gc import multihook
from pypytools.gc import custom

MODULES_TO_PATCH = [multihook, custom]

@pytest.fixture
def fakegc(monkeypatch):
    mygc = FakeGc()
    for mod in MODULES_TO_PATCH:
        monkeypatch.setattr(mod, 'gc', mygc)
    return mygc


class FakeGc(object):

    class Hooks(object):
        on_gc_minor = None
        on_gc_collect_step = None
        on_gc_collect = None

    def __init__(self):
        self.hooks = self.Hooks()
        self._enabled = True

    def isenabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False


    # these are not part of the gc API, but are used to simulate events
    def fire_minor(self, stats):
        if self.hooks.on_gc_minor:
            self.hooks.on_gc_minor(stats)

    def fire_step(self, stats):
        if self.hooks.on_gc_collect_step:
            self.hooks.on_gc_collect_step(stats)

    def fire_collect(self, stats):
        if self.hooks.on_gc_collect:
            self.hooks.on_gc_collect(stats)


class TestFakeGc:

    def test_fire_hooks(self, fakegc):
        minors = []
        steps = []
        collects = []

        fakegc.fire_minor('minor 1')
        fakegc.fire_step('step 1')
        fakegc.fire_collect('collect 1')

        fakegc.hooks.on_gc_minor = minors.append
        fakegc.hooks.on_gc_collect_step = steps.append
        fakegc.hooks.on_gc_collect = collects.append

        fakegc.fire_minor('minor 2')
        fakegc.fire_step('step 2')
        fakegc.fire_collect('collect 2')

        assert minors == ['minor 2']
        assert steps == ['step 2']
        assert collects == ['collect 2']

    def test_enable_disable(self, fakegc):
        assert fakegc.isenabled()
        fakegc.disable()
        assert not fakegc.isenabled()
        fakegc.enable()
        assert fakegc.isenabled()
