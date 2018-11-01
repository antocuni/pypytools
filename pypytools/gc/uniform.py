"""
The goal of this GC strategy is to spread the GC activity as evenly as
possible.
"""
import time
from collections import deque


KB = 1024.0
MB = KB * KB

class UniformGcStrategy(object):

    # MAJOR_COLLECT is roughly equivalent to PYPY_GC_MAJOR_COLLECT. The normal
    # PyPy GC uses PYPY_GC_MAJOR_COLLECT to compute the threshold for when to
    # start a major collection: however, with UniformGc a major collection
    # will take a lot of time to complete, and in the meantime the user
    # program an callocate more.  So, we use MAJOR_COLLECT to compute the
    # value of target_allocated_mem
    MAJOR_COLLECT = 1.82  # roughly PYPY_GC_MAJOR_COLLECT
    MIN_TARGET = 10*MB    # roughly PYPY_GC_MIN

    # if we are using too much memory, try to run a GC step every
    # EMERGENCY_DELAY, and hope to finish soon. This might happen if we
    # suddenly allocate much more than expected, or if a GC cycle takes more
    # than gc_estimated_t. If EMERGENCY_DELAY is too high, the risk is to
    # allocate faster than the GC can free, and have an endless loop. If it's
    # too low, we risk to dedicate too much time to the GC and block important
    # activity in the user program
    EMERGENCY_DELAY = 0.01 # 10 ms

    def __init__(self, initial_mem):
        self.last_mem = initial_mem   # last known value of used memory
        self.last_t = time.time()     # time of the last tick
        self.alloc_rate = None        # estimated allocation rate, bytes/s

        # the memory allocated by the user program SINCE THE START of the
        # current collection.  Note that it is NOT equivalent to
        # "current_mem-starting_mem", because during the sweeping phases the
        # current_mem shrinks.  We aim to finish the GC cycle before
        # allocated_mem > target_allocated_mem
        # Note that both are adjusted during a start_major()
        self.allocated_mem = 0
        self.target_allocated_mem = 0

        # we don't know how much it will take to complete a GC cycle; we just
        # guess reasonable numbers here, they will be automatically adjusted
        # as soon as we complete our first collection
        self.gc_estimated_t = 0.01 # 10 ms, just a random guess
        self.gc_last_step_duration = 0.001 # another random guess
        self.gc_last_step_t = self.last_t

        # number of major collections fully done so far. Not used by anything,
        # just a statistics
        self.n_majors = -1 # increased to 0 when we start_another_major()
        self.start_another_major(initial_mem)


    # ======================================================================
    # Public API
    # ======================================================================

    # in all the code, the parameter "mem" indicates the memory currently used
    def tick(self, mem):
        """
        Regularly called by the user program. Return True if it is time to run a
        GC step.
        """
        try:
            cur_t = time.time()
            delta_mem = mem - self.last_mem
            self.allocated_mem += delta_mem
            self.update_alloc_rate(cur_t, mem)
            if cur_t >= self.get_time_for_next_step(self.allocated_mem):
                return True
            return False
        finally:
            self.last_t = cur_t
            self.last_mem = mem

    def record_gc_step(self, mem, duration, stats):
        """
        Call this AFTER you call gc.collect_step
        """
        self.gc_cumul_t += duration
        self.gc_steps += 1
        self.last_mem = mem
        if stats.major_is_done:
            self.start_another_major(mem)

    # ======================================================================
    # Private API
    # ======================================================================

    def start_another_major(self, mem):
        self.n_majors += 1
        self.gc_cumul_t = 0
        self.gc_steps = 0
        self.allocated_mem = 0
        self.compute_target(mem)

    # XXX: kill this and merge with gc_reset
    def compute_target(self, mem):
        # MAJOR_COLLECT is a k>1, relative to mem; but we want the delta, so
        # we just use MAJOR_COLLECT-1
        self.target_allocated_mem = max(mem * (self.MAJOR_COLLECT-1),
                                        self.MIN_TARGET)

    def update_alloc_rate(self, cur_t, mem):
        delta_t = cur_t - self.last_t
        delta_mem = mem - self.last_mem
        cur_alloc_rate = delta_mem / delta_t # bytes/s
        cur_alloc_rate = max(1, cur_alloc_rate) # avoid ZeroDivisionError later
        if self.alloc_rate is None:
            self.alloc_rate = cur_alloc_rate
        else:
            # equivalent to an exponential moving average
            self.alloc_rate = (self.alloc_rate + cur_alloc_rate) / 2.0

    def get_time_for_next_step(self, allocated_mem):
        """
        The goal is to spread GC activity as evenly as possible, i.e.  for any
        given timespan, the GC/user ratio should be roughly the same.

        We know how much time we spent in the GC for the last step, so now we
        let the user program to run enough to keep the desired ratio.

        What is the ratio? We don't know, but we estimate it based on:

          - the total (estimated) time needed for the GC to complete

          - the total (estimated) time we have before we reach the target,
            given the current allocation rate

        The formula is derived as follows:
            let p be the gc/user ration for the complete GC cycle:
                p = total_gc_time / total_time
        
            we want to maintain the ratio for a given step:
                p = (gc_time) / (gc_time + wait_time) ===>
                wait_time = gc_time * (1-p)/p
        """
        if allocated_mem >= self.target_allocated_mem:
            return self.gc_last_step_t + self.EMERGENCY_DELAY
        gc_time_left = self.gc_estimated_t - self.gc_cumul_t
        assert gc_time_left > 0, 'XXX what to do?'
        mem_left = self.target_allocated_mem - allocated_mem
        time_left = (mem_left / self.alloc_rate) + gc_time_left
        p = gc_time_left / time_left
        wait_t = self.gc_last_step_duration * (1-p)/p
        return self.gc_last_step_t + wait_t
