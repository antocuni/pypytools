"""
Improve PyPy's GC hooks and make it possible to have multiple callbacks
"""
import gc
import types

class MultiHook(object):
    """
    This is the actual class which is installed as GC hooks. It is not meant
    to be used directly, but to be manipulates by GcHooks()
    """

    def __init__(self):
        self.hooks = [] # list of GcHooks instances
        self._update_callbacks()

    def add(self, gchooks):
        self.hooks.append(gchooks)
        self._update_callbacks()

    def remove(self, gchooks):
        self.hooks.remove(gchooks)
        self._update_callbacks()

    def _check_other_hooks(self):
        # Safety check to avoid disabling other hooks by mistake: the only
        # permitted hooks are the ones installed by us, i.e. bound methods of
        # "self". If we find extraneous hooks, complain
        def check(m):
            return (m is None or
                    (isinstance(m, types.MethodType) and m.__self__ is self))

        if not (check(gc.hooks.on_gc_minor) and
                check(gc.hooks.on_gc_collect_step) and
                check(gc.hooks.on_gc_collect)):
            raise ValueError("It seems other GC hooks are already installed. "
                             "Consider to use multihook everywhere.")

    def _update_callbacks(self):
        self._check_other_hooks()
        self.minor_callbacks = []
        self.collect_step_callbacks = []
        self.collect_callbacks = []
        for h in self.hooks:
            cb = getattr(h, 'on_gc_minor', None)
            if cb:
                self.minor_callbacks.append(cb)

            cb = getattr(h, 'on_gc_collect_step', None)
            if cb:
                self.collect_step_callbacks.append(cb)

            cb = getattr(h, 'on_gc_collect', None)
            if cb:
                self.collect_callbacks.append(cb)

        if self.minor_callbacks:
            gc.hooks.on_gc_minor = self.on_gc_minor

        if self.collect_step_callbacks:
            gc.hooks.on_gc_collect_step = self.on_gc_collect_step

        if self.collect_callbacks:
            gc.hooks.on_gc_collect = self.on_gc_collect
    
    def on_gc_minor(self, stats):
        for cb in self.minor_callbacks:
            cb(stats)

    def on_gc_collect_step(self, stats):
        for cb in self.collect_step_callbacks:
            cb(stats)

    def on_gc_collect(self, stats):
        for cb in self.collect_callbacks:
            cb(stats)
