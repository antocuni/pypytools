import pytest
from pypytools import IS_PYPY
from pypytools.gc.custom import CustomGc, DefaultGc
from pypytools.gc.testing.test_fakegc import fakegc
from pypytools.gc.testing.test_multihook import GcStatistics


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
