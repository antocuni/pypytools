import sys
import gc
from pypytools import IS_PYPY
from pypytools.gc.multihook import GcHooks

KB = 1024.0
MB = KB * KB

class CustomGc(GcHooks):    
    """
    GC with custom logic which is triggered by hooks. Override on_gc_minor to
    implement your custom logic
    """

    def __init__(self):
        self._isenabled = False

    def isenabled(self):
        return self._isenabled

    def enable(self):
        if self._isenabled:
            return
        gc.disable()
        self._isenabled = True
        super(CustomGc, self).enable()

    def disable(self):
        if not self._isenabled:
            return
        gc.enable()
        self._isenabled = False
        super(CustomGc, self).disable()



class DefaultGc(CustomGc):
    """
    Custom GC which mimimcs the default logic of incminimark
    """

    MAJOR_COLLECT = 1.82      # same as PYPY_GC_MAJOR_COLLECT
    MIN_THRESHOLD = 4*8 * MB  # same as PYPY_GC_MIN
    MAX_GROWTH = 1.4          # same as PYPY_GC_GROWTH

    def __init__(self):
        super(DefaultGc, self).__init__()
        self.major_in_progress = False
        self.threshold = 0
        self.update_threshold(0)

    def update_threshold(self, mem):
        self.threshold = max(self.MIN_THRESHOLD,
                             min(mem * self.MAJOR_COLLECT,
                                 self.threshold * self.MAX_GROWTH))

    def on_gc_minor(self, stats):
        if self.major_in_progress:
            step_stats = gc.collect_step()
            if step_stats.major_is_done:
                self.major_in_progress = False
                self.update_threshold(stats.total_memory_used)

        elif stats.total_memory_used > self.threshold:
            self.major_in_progress = True
            gc.collect_step()
