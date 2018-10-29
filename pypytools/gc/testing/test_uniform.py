from pypytools.gc.uniform import UniformGcStrategy

class TestUniformGcStrategy(object):

    def new(self, **kwds):
        s = UniformGcStrategy()
        s.__dict__.update(**kwds)
        return s

    def test_target_memory(self):
        s = self.new(MAJOR_COLLECT=1.8,
                     GROWTH=1.5,
                     target_memory=200)
        #
        s.compute_target_memory(mem=100)
        assert s.target_memory == 180 # 100*1.8
        #
        s.compute_target_memory(mem=500)
        assert s.target_memory == 270 # 180*1.5, limited by GROWTH
