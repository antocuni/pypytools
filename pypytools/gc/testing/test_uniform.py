import time
from pytest import approx
from freezegun import freeze_time
from pypytools.gc.uniform import UniformGcStrategy

class FakeGcCollectStats(object):

    def __init__(self, major_is_done):
        self.major_is_done = major_is_done

class TestUniformGcStrategy(object):

    def new(self, initial_mem=0, **kwds):
        # we call __new__ and __init__ separately so that we can patch **kwds
        # before they are used in the __init__ (e.g., MIN_TARGET)
        s = UniformGcStrategy.__new__(UniformGcStrategy)
        s.__dict__.update(**kwds)
        s.__init__(initial_mem)
        return s

    def fakestats(self, is_done=False):
        return FakeGcCollectStats(is_done)

    def test_target_allocated_mem(self):
        s = self.new(MAJOR_COLLECT=1.8, MIN_TARGET=50)
        assert s.target_mem == 50
        assert s.target_allocated_mem == 50

        s.start_another_major(mem=100)
        assert s.target_mem == 180 # 100*1.8
        assert s.target_allocated_mem == 80

        s.start_another_major(mem=20)
        assert s.target_mem == 50 # MIN_TARGET
        assert s.target_allocated_mem == 30

    def test_estimated_gc(self):
        s = self.new(MAJOR_COLLECT=1.8, MIN_TARGET=1)
        # the last GC took 1s for a target_mem of 100
        s.target_mem = 100
        s.gc_cumul_t = 1.0

        s.start_another_major(mem=100)
        assert s.target_mem == 180
        assert s.gc_estimated_t == 1.8

    def test_alloc_rate(self):
        with freeze_time('2018-01-01') as freezer:
            s = self.new(initial_mem=100)
            freezer.tick(0.5)           # 0.5 second
            s.tick(mem=150)             # delta_mem == 50
            assert s.alloc_rate == 100  # 50/0.5 bytes/s

            freezer.tick(2)             # 2 seconds
            s.tick(mem=250)             # delta_mem == 100
            assert s.alloc_rate == 75   # because of the average

            freezer.tick(1)
            s.tick(mem=100)             # negative delta_mem
            assert s.alloc_rate == 38   # capped at 1

    def test_alloc_rate_nonzero(self):
        s = self.new(initial_mem=100)
        s.tick(mem=90)
        assert s.alloc_rate == 1

    def test_get_time_for_next_step(self):
        s = self.new(initial_mem=0)
        # time to allocate 900 bytes:  9 s
        # time estimated for the GC:   1 s
        # total estimated time:       10 s
        # GC / total:                 10%
        s.target_allocated_mem = 900.0
        s.allocated_mem = 0
        s.alloc_rate = 100.0 # bytes/s
        s.gc_estimated_t = 1
        # If the last step took 0.01 s, I wait for 0.09 to keep the expected
        # GC/total ration
        s.gc_last_step_t = 42
        s.gc_last_step_duration = 0.01
        t = s.get_time_for_next_step()
        assert t == 42.09

        # the time doesn't change if I allocate at the expected rate
        s.allocated_mem = 300
        s.gc_last_step_t = 42.03
        t = s.get_time_for_next_step()
        assert t == 42.09

        # the result changes accordingly to the allocation rate: if I allocate
        # slower, I have more time to finish the collection
        s.allocated_mem = 0
        s.alloc_rate = 10.0
        s.gc_last_step_t = 42
        t = s.get_time_for_next_step()
        assert t == 42.9

        # if I allocate faster, I need to hurry up
        s.alloc_rate = 1000.0
        t = s.get_time_for_next_step()
        assert t == 42.009

    def test_emergency_delay(self):
        # we are using too much memory and we have not finished the GC yet
        s = self.new(EMERGENCY_DELAY=3)
        s.gc_last_step_t = 39
        s.allocated_mem = 100
        s.target_allocated_mem = 100
        assert s.get_time_for_next_step() == 42

    def test_allocated_mem(self):
        s = self.new(initial_mem=500)
        assert s.allocated_mem == 0
        
        s.tick(mem=600)
        assert s.allocated_mem == 100
        s.tick(mem=700)
        assert s.allocated_mem == 200

        # simulate a sweep step, in which the mem usage decrease
        s.record_gc_step(mem=650, duration=0, stats=self.fakestats())
        s.tick(mem=690) # mem is back at 690, +40 bytes
        assert s.allocated_mem == 240

    def test_should_collect(self):
        with freeze_time('2018-01-01') as freezer:
            s = self.new(initial_mem=0)
            # with the following params and an alloc_rate of 100 bytes/s, the
            # GC takes an estimated 10% of the time
            s.target_allocated_mem = 900.0
            s.gc_estimated_t = 1
            s.gc_last_step_duration = 0.01

            # so, we expect to run 9 iterations before doing one step
            mem = 0
            i = 0
            while True:
                freezer.tick(0.01)
                i += 1
                mem += 1
                should_collect = s.tick(mem=mem)
                assert s.alloc_rate == approx(100) # floating point rounding :(
                assert s.last_t == time.time()
                assert s.last_mem == mem
                if should_collect:
                    break
            assert i == 9

    def test_record_gc_step(self):
        with freeze_time('2018-01-01') as freezer:
            s = self.new(initial_mem=0,
                         MAJOR_COLLECT=1.8,
                         MIN_TARGET=50)
            assert s.n_majors == 0

            t = time.time()
            s.record_gc_step(100, 2, self.fakestats(is_done=False))
            s.record_gc_step(110, 3, self.fakestats(is_done=False))
            s.record_gc_step(120, 1, self.fakestats(is_done=False))
            assert s.gc_cumul_t == 2+3+1
            assert s.gc_steps == 3
            assert s.last_mem == 120
            assert s.last_t == t
            assert s.gc_last_step_t == t

            freezer.tick(1)
            s.record_gc_step(80, 1, self.fakestats(is_done=True))
            assert s.n_majors == 1
            assert s.gc_cumul_t == 0
            assert s.gc_steps == 0
            assert s.last_mem == 80
            assert s.last_t == t+1
            assert s.gc_last_step_t == t+1
            assert s.target_allocated_mem == 80*0.8

    def test_adjust_gc_estimated_t(self):
        s = self.new(initial_mem=0, ESTIMATED_OVERFLOW_FACTOR=1.2)
        s.gc_estimated_t = 10.0
        stats = self.fakestats(is_done=False)
        s.record_gc_step(mem=100, duration=9, stats=stats)
        assert s.gc_estimated_t == 10.0

        # gc_cumul_t => 11.5, adjust the estimate
        s.record_gc_step(mem=100, duration=1.5, stats=stats)
        assert s.gc_estimated_t == 12.0

        # if gc_cumul_t is much bigger than the estimate, a single
        # *=ESTIMATED_OVERFLOW_FACTOR is not enouch; keep multiplying until
        # the estimate is bigger than the measured
        # gc_cumul_t ==> 14.5
        s.record_gc_step(mem=100, duration=4.5, stats=stats)
        assert s.gc_estimated_t == 12.0 * 1.2 * 1.2
