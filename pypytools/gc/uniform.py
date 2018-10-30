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
    # program can callocate more.  So, we use MAJOR_COLLECT to compute the
    # value of target_memory: the goal is to complete a full major GC cycle
    # just before we reach target_memory.  Once we have the target_memory, we
    # can compute the actual threshold for when to *start* a GC cycle
    MAJOR_COLLECT = 1.82  # roughly PYPY_GC_MAJOR_COLLECT
    GROWTH = 1.4          # same as PYPY_GC_GROWTH
    MIN_TARGET = 10*MB    # roughly PYPY_GC_MIN

    def __init__(self, initial_mem):
        self.last_time = time.time()
        self.last_mem = initial_mem
        self.alloc_rate = None
        self.target_memory = self.MIN_TARGET

    # ======================================================================
    # Public API
    # ======================================================================

    # in all the code, the parameter "mem" indicates the memory currently used
    def tick(self, mem):
        """
        Regularly called by the user program. Return True if it is time to run a
        GC step.
        """
        cur_time = time.time()
        self.update_alloc_rate(cur_time, mem)

        self.last_time = cur_time
        self.last_mem = mem
    

    # ======================================================================
    # Private API
    # ======================================================================

    def compute_target_memory(self, mem):
        # MIN_TARGET <= mem * MAJOR_COLLECT <= target_memory * GROWTH
        self.target_memory = max(
            self.MIN_TARGET,
            min(mem * self.MAJOR_COLLECT,
                self.target_memory * self.GROWTH))

    def update_alloc_rate(self, cur_time, mem):
        delta_t = cur_time - self.last_time
        delta_mem = mem - self.last_mem
        cur_alloc_rate = delta_mem / delta_t # bytes/s
        cur_alloc_rate = max(0, cur_alloc_rate) # never use a negative alloc_rate
        if self.alloc_rate is None:
            self.alloc_rate = cur_alloc_rate
        else:
            # equivalent to an exponential moving average
            self.alloc_rate = (self.alloc_rate + cur_alloc_rate) / 2.0
