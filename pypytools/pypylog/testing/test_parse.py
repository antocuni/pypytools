import pytest
import textwrap
from cStringIO import StringIO
from pypytools.pypylog import parse
from pypytools.pypylog import model
from pypytools.pypylog.model import Event

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
            Event('foo', 0x000, 0x123, depth=0),
            Event('bar', 0x456, 0x789, depth=0)
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
            Event('bar', 0x200, 0x300, depth=1),
            Event('foo', 0x000, 0x400, depth=0),
            Event('baz', 0x500, 0x600, depth=0)
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
            Event('foo', 0x000, 0x200, depth=0),
            Event('foo', 0x700, 0x800, depth=0)
        ]
        assert log.sections['bar'] == [
            Event('bar', 0x300, 0x400, depth=0),
            Event('bar', 0x500, 0x600, depth=0)
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
