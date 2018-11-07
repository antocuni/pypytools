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
        self._steps_to_major = 3 # number of collect_step to call before
                                 # finishing a major collection

    def isenabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def collect_step(self):
        self._steps_to_major -= 1
        if self._steps_to_major == 0:
            # in PyPy, the last gc.collect_step does not invoke any GC hook,
            # because it runs the app-level finalizers
            self._steps_to_major = 3
            return FakeCollectStepStats(major_is_done=True)
        else:
            stats = FakeCollectStepStats(major_is_done=False)
            # in PyPy, gc.collect_step also does a minor collection, so the effect
            self.fire_minor(FakeMinorStats(total_memory_used=42))
            self.fire_step(stats)
            return stats

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


class FakeMinorStats(object):

    def __init__(self, total_memory_used):
        self.total_memory_used = total_memory_used


class FakeCollectStepStats(object):

    def __init__(self, major_is_done):
        self.major_is_done = major_is_done


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

    def test_collect_step(self, fakegc):
        steps = []
        fakegc.hooks.on_gc_collect_step = steps.append
        fakegc._steps_to_major = 3
        n = 0
        while True:
            n += 1
            stats = fakegc.collect_step()
            if stats.major_is_done:
                break
            assert n < 100, 'endless loop?'
        assert n == 3
        assert len(steps) == 2 # the last collect_step doesn't call the hook
