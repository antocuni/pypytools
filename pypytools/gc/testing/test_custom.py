import pytest
from pypytools import IS_PYPY
from pypytools.gc.custom import CustomGc, DefaultGc
from pypytools.gc.testing.test_fakegc import fakegc, FakeMinorStats
from pypytools.gc.testing.test_multihook import GcStatistics, mh

class TestCustomGc:

    def test_enable_disable(self, fakegc):
        class MyGc(CustomGc):

            def __init__(self):
                self.minors = []
                super(MyGc, self).__init__()

            def on_gc_minor(self, stats):
                self.minors.append(stats)

        mygc = MyGc()
        assert not mygc.isenabled()
        assert fakegc.isenabled()
        fakegc.fire_minor('AAA')
        assert mygc.minors == []

        mygc.enable()
        assert mygc.isenabled()
        assert not fakegc.isenabled()
        fakegc.fire_minor('BBB')
        assert mygc.minors == ['BBB']

        mygc.disable()
        assert not mygc.isenabled()
        assert fakegc.isenabled()
        fakegc.fire_minor('CCC')
        assert mygc.minors == ['BBB'] # CCC is not there


class TestDefaultGc:

    def test_threshold(self):
        class MyGc(DefaultGc):
            MAJOR_COLLECT = 2.0
            MIN_THRESHOLD = 100
            MAX_GROWTH = 1.5

        mygc = MyGc()
        assert mygc.threshold == 100

        mygc.update_threshold(mem=200)
        assert mygc.threshold == 150 # capped by MAX_GROWTH

        mygc.update_threshold(mem=80)
        assert mygc.threshold == 160 # mem * MAJOR_COLLECT

    def test_run_steps(self, fakegc):
        class MyGc(DefaultGc):
            MAJOR_COLLECT = 2.0
            MIN_THRESHOLD = 100
            MAX_GROWTH = 100

        def S(mem):
            return FakeMinorStats(total_memory_used=mem)

        stats = GcStatistics()
        mygc = MyGc()
        stats.enable()
        mygc.enable()

        assert mygc.threshold == 100
        fakegc._steps_to_major = 3
        fakegc.fire_minor(S(mem=50))
        assert not mygc.major_in_progress
        assert len(stats.steps) == 0

        fakegc.fire_minor(S(mem=101))
        assert mygc.major_in_progress
        assert len(stats.steps) == 1

        fakegc.fire_minor(S(mem=102))
        assert mygc.major_in_progress
        assert len(stats.steps) == 2

        fakegc.fire_minor(S(mem=103))
        assert not mygc.major_in_progress
        assert len(stats.steps) == 2 # the last collect_step doesn't call the hook
        assert mygc.threshold == 206

        fakegc.fire_minor(S(mem=104))
        assert not mygc.major_in_progress
        assert len(stats.steps) == 2 # no more steps

    def test_nogc(self, fakegc):
        class MyGc(DefaultGc):
            MAJOR_COLLECT = 2.0
            MIN_THRESHOLD = 100
            MAX_GROWTH = 100

        def S(mem):
            return FakeMinorStats(total_memory_used=mem)

        stats = GcStatistics()
        mygc = MyGc()
        stats.enable()
        mygc.enable()

        fakegc.fire_minor(S(mem=101))
        assert len(stats.steps) == 1
        with mygc.nogc():
            fakegc.fire_minor(S(mem=102))
            assert len(stats.steps) == 1 # don't do a collect_step here
        fakegc.fire_minor(S(mem=102))
        assert len(stats.steps) == 2 # collect_step done as usual


    @pytest.mark.skip('flaky test')
    @pytest.mark.skipif(not IS_PYPY, reason='PyPy only test')
    def test_real_gc(self):
        import gc # real pypy GC
        from collections import deque
        
        def allocate_some():
            # allocate and discard a total of 100 MB
            d = deque(maxlen=5)
            for i in range(100):
                s = chr(i%256) * (1024*1024) # 1MB
                d.append(s)

        stats = GcStatistics()
        stats.enable()

        # check that allocate_some triggers the GC
        allocate_some()
        assert len(stats.collects) >= 1

        # now, disable the PyPy GC and check that it's not triggered. This
        # works only on the PyPy "gc-disable" branch for now
        mygc = DefaultGc() # custom GC
        gc.disable()
        gc.collect() # start from "fresh"
        stats.reset()

        # the PyPy GC is disabled, no collections
        allocate_some()
        assert len(stats.collects) == 0

        # enable the custom GC and check that it collects
        mygc.enable()
        allocate_some()
        assert len(stats.collects) >= 1

    @pytest.mark.skipif(IS_PYPY, reason='CPython only test')
    def test_dont_disable_on_CPython(self, mh):
        import gc
        # if we are on CPython, we want DefaultGc to do nothing. In
        # particular, it should NOT disable the builtin GC (because else
        # nobody is going to run finalizers)
        mygc = DefaultGc()
        mygc.enable()
        assert gc.isenabled()
