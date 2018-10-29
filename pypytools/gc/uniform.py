"""
The goal of this GC strategy is to spread the GC activity as evenly as
possible.
"""

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
    
    MAJOR_COLLECT = 1.82  # same as PYPY_GC_MAJOR_COLLECT
    GROWTH = 1.4          # same as PYPY_GC_GROWTH

    def __init__(self):
        self.target_memory = 10 * MB # reasonable value for the first collection

    # in all the code, the parameter "mem" indicates the memory currently used
    def compute_target_memory(self, mem):
        self.target_memory = min(mem * self.MAJOR_COLLECT,
                                 self.target_memory * self.GROWTH)
