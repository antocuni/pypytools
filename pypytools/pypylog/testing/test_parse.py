import pytest
import textwrap
from cStringIO import StringIO
from pypytools.pypylog import parse

class TestFlatParser(object):

    def parse(self, log):
        log = textwrap.dedent(log)
        f = StringIO(log)
        p = parse.FlatParser()
        p.feed(f)
        return p.result

    def test_simple(self):
        log = self.parse("""
        [123] {foo
        [456] foo}
        [789] {bar
        [0ab] bar}
        """)
        assert log == [
            ('foo', 0x123, 0x456),
            ('bar', 0x789, 0x0ab)
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
        assert log == [
            ('bar', 0x200, 0x300),
            ('foo', 0x100, 0x400),
            ('baz', 0x500, 0x600)
        ]
