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
        [123] {foo
        [456] foo}
        [789] {bar
        [0ab] bar}
        """)
        assert log.all_events() == [
            Event('foo', 0x123, 0x456),
            Event('bar', 0x789, 0x0ab)
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
        [100] {foo
        [200] {bar
        [300] bar}
        [400] foo}
        [500] {baz
        [600] baz}
        """)
        assert log.all_events() == [
            Event('bar', 0x200, 0x300),
            Event('foo', 0x100, 0x400),
            Event('baz', 0x500, 0x600)
        ]

    def test_GroupedPyPyLog(self):
        text = """
        [100] {foo
        [200] foo}
        [300] {bar
        [400] bar}
        [500] {bar
        [600] bar}
        [700] {foo
        [800] foo}
        """
        log = self.parse(text, model.GroupedPyPyLog())
        assert sorted(log.sections.keys()) == ['bar', 'foo']
        assert log.sections['foo'] == [
            Event('foo', 0x100, 0x200),
            Event('foo', 0x700, 0x800)
        ]
        assert log.sections['bar'] == [
            Event('bar', 0x300, 0x400),
            Event('bar', 0x500, 0x600)
        ]
