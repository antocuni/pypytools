from pypytools.pypylog import model

class TestSeries(object):

    def test_from_points(self):
        s = model.Series.from_points([(0, 1), (1, 2), (2, 4), (3, 8)])
        assert len(s) == 4
        assert list(s.X) == [0, 1, 2, 3]
        assert list(s.Y) == [1, 2, 4, 8]

    def test_iter(self):
        plist = [(0, 1), (1, 2), (2, 4), (3, 8)]
        s = model.Series.from_points(plist)
        plist2 = list(s)
        assert plist == plist2 

    def test_get_set_item(self):
        s = model.Series.from_points([(0, 0), (1, 1)])
        assert s[0] == (0, 0)
        assert s[1] == (1, 1)
        s[1] = (2, 2)
        assert s[1] == (2, 2)


def test_make_step_chart():
    events = [
        model.Event('gc',  100, 120, depth=0),
        model.Event('jit', 130, 135, depth=0)
    ]
    s = model.make_step_chart(events)
    points = list(s)
    assert points == [
        (100, 0),
        (100, 20),
        
        (100, 20),
        (120, 20),

        (120, 20),
        (120, 0),

        (130, 0),
        (130, 5),

        (130, 5),
        (135, 5),

        (135, 5),
        (135, 0),
    ]
