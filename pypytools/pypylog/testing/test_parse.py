import pytest
import textwrap
from cStringIO import StringIO
from pypytools.pypylog import parse
from pypytools.pypylog import model
from pypytools.pypylog.model import Event, GcMinor, GcCollectStep

class TestFlatParser(object):

    def parse(self, text, log=None):
        text = textwrap.dedent(text)
        f = StringIO(text)
        return parse.flat(f, log)

    def test_simple(self):
        log = self.parse("""
        [ff000] {foo
        [ff123] foo}
        [ff456] {bar
        [ff789] bar}
        """)
        assert log.all_events() == [
            Event('ff000', 'foo', 0x000, 0x123),
            Event('ff456', 'bar', 0x456, 0x789)
        ]

    def test_mismatch(self):
        # raise an error for now, but I think there might be real cases in
        # which this happens
        log = """
        [123] {foo
        [789] {bar
        [456] foo}
        [0ab] bar}
        """
        pytest.raises(parse.ParseError, "self.parse(log)")

    def test_nested(self):
        log = self.parse("""
        [ff000] {foo
        [ff200] {bar
        [ff300] bar}
        [ff400] foo}
        [ff500] {baz
        [ff600] baz}
        """)
        assert log.all_events() == [
            Event('ff200', 'bar', 0x200, 0x300),
            Event('ff000', 'foo', 0x000, 0x400),
            Event('ff500', 'baz', 0x500, 0x600)
        ]

    def test_GroupedPyPyLog(self):
        text = """
        [ff000] {foo
        [ff200] foo}
        [ff300] {bar
        [ff400] bar}
        [ff500] {bar
        [ff600] bar}
        [ff700] {foo
        [ff800] foo}
        """
        log = self.parse(text, model.GroupedPyPyLog())
        assert sorted(log.sections.keys()) == ['bar', 'foo']
        assert log.sections['foo'] == [
            Event('ff000', 'foo', 0x000, 0x200),
            Event('ff700', 'foo', 0x700, 0x800)
        ]
        assert log.sections['bar'] == [
            Event('ff300', 'bar', 0x300, 0x400),
            Event('ff500', 'bar', 0x500, 0x600)
        ]


class TestGcParser(object):
    
    def parse(self, text, log=None):
        text = textwrap.dedent(text)
        f = StringIO(text)
        return parse.gc(f, log)

    def test_gc_minor(self):
        text = """
        [ff000] {gc-minor
        [ff001] {gc-minor-walkroots
        [ff002] gc-minor-walkroots}
        minor collect, total memory used: 1000
        number of pinned objects: 0
        [ff100] gc-minor}
        [ff200] {gc-minor
        [ff201] {gc-minor-walkroots
        [ff202] gc-minor-walkroots}
        minor collect, total memory used: 2000
        number of pinned objects: 0
        [ff300] gc-minor}
        """
        log = self.parse(text, model.GroupedPyPyLog())
        assert log.sections['gc-minor'] == [
            GcMinor('ff000', 'gc-minor', 0x000, 0x100, memory=1000),
            GcMinor('ff200', 'gc-minor', 0x200, 0x300, memory=2000),
        ]

    def test_gc_collect_step(self):
        text = """
        [ff000] {gc-collect-step
        starting gc state:  SCANNING
        stopping, now in gc state:  MARKING
        [ff100] gc-collect-step}
        """
        log = self.parse(text)
        assert log.all_events() == [
            GcCollectStep('ff000', 'gc-collect-step', 0x000, 0x100,
                          phase='SCANNING')
            ]

def test_parse_frequency():
    pf = parse.parse_frequency
    assert pf('40') == 40
    assert pf('40hz') == 40
    assert pf('40Hz') == 40
    assert pf('40 Hz') == 40
    assert pf('40 Hz ') == 40
    assert pf('40 KHz') == 40e3
    assert pf('40 MHz') == 40e6
    assert pf('40 GHz') == 40e9
    pytest.raises(ValueError, "pf('')")
