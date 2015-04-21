from pypytools.cast import as_signed

def test_as_signed():
    assert as_signed(0xFF, 8) == -1
    assert as_signed(0xFF, 9) == 255
    assert as_signed(0xFFFF, 16) == -1
    assert as_signed(0b1000, 4) == -8

