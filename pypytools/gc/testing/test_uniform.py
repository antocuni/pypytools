from freezegun import freeze_time
from pypytools.gc.uniform import UniformGcStrategy


class TestUniformGcStrategy(object):

    def new(self, initial_mem=0, **kwds):
        s = UniformGcStrategy(initial_mem)
        s.__dict__.update(**kwds)
        return s

    def test_target_memory(self):
        s = self.new(MAJOR_COLLECT=1.8,
                     GROWTH=1.5,
                     MIN_TARGET=50,
                     target_memory=200)
        #
        s.compute_target_memory(mem=100)
        assert s.target_memory == 180 # 100*1.8
        #
        s.compute_target_memory(mem=500)
        assert s.target_memory == 270 # 180*1.5, limited by GROWTH
        #
        s.compute_target_memory(mem=10)
        assert s.target_memory == 50  # MIN_TARGET

    def test_alloc_rate(self):
        with freeze_time('2018-01-01') as freezer:
            s = self.new(initial_mem=100)

            freezer.tick(0.5)           # 0.5 second
            s.tick(mem=150)             # delta_mem == 50
            assert s.alloc_rate == 100  # 50/0.5 bytes/s
            #
            freezer.tick(2)             # 2 seconds
            s.tick(mem=250)             # delta_mem == 100
            assert s.alloc_rate == 75   # because of the average
            #
            freezer.tick(1)
            s.tick(mem=100)             # negative delta_mem
            assert s.alloc_rate == 37.5 # capped at 0
