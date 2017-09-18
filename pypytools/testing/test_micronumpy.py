import pypytools
from pypytools.compat import micronumpy as unp

eq = unp.array_equal

class TestMicronumpy(object):

    def test_IS_MICRONUMPY(self):
        assert unp.IS_MICRONUMPY == pypytools.IS_PYPY

    def test_all(self):
        a = unp.array([1, 2, 3])
        b = unp.array([1, 2, 0])
        assert unp.all(a)
        assert not unp.all(b)

    def test_any(self):
        a = unp.array([0, 0, 0])
        b = unp.array([0, 0, 1])
        assert not unp.any(a)
        assert unp.any(b)

    def test_argmax(self):
        a = unp.array([100, 101, 102])
        assert unp.argmax(a) == 2

    def test_argmin(self):
        a = unp.array([100, 101, 102])
        assert unp.argmin(a) == 0

    def test_argsort(self):
        a = unp.array([101, 102, 100])
        assert eq(unp.argsort(a), [2, 0, 1])

    def test_choose(self):
        choices = unp.array([[0, 1, 2, 3],
                             [10, 11, 12, 13],
                             [20, 21, 22, 23],
                             [30, 31, 32, 33]])
        out = unp.choose(unp.array([2, 3, 1, 0]), choices)
        assert eq(out, [20, 31, 12,  3])

    def test_clip(self):
        a = unp.array([1, 2, 3, 4, 5, 6])
        assert eq(unp.clip(a, 2, 5), [2, 2, 3, 4, 5, 5])

    def test_copy(self):
        a = unp.array([1, 2, 3])
        b = unp.copy(a)
        assert a is not b
        assert eq(a, b)

    def test_cumprod(self):
        a = unp.array([1, 2, 3, 4])
        assert eq(unp.cumprod(a), [1, 2, 6, 24])

    def test_cumsum(self):
        a = unp.array([1, 2, 3, 4])
        assert eq(unp.cumsum(a), [1, 3, 6, 10])

    def test_diagonal(self):
        a = unp.array([[1, 2, 3],
                       [4, 5, 6],
                       [7, 8, 9]])
        assert eq(unp.diagonal(a), [1, 5, 9])

    def test_max(self):
        a = unp.array([1, 2, 3])
        assert unp.max(a) == 3

    def test_min(self):
        a = unp.array([3, 1, 2])
        assert unp.min(a) == 1

    def test_nonzero(self):
        a = unp.array([100, 0, 102, 103])
        (idx,) = unp.nonzero(a)
        assert eq(idx, [0, 2, 3])

    def test_prod(self):
        a = unp.array([1, 2, 3])
        assert unp.prod(a) == 6

    def test_ptp(self):
        a = unp.array([1, 2, 3])
        assert unp.ptp(a) == 2

    def test_put(self):
        a = unp.array([0, 1, 2, 3, 4])
        unp.put(a, [0, 2], [-44, -55])
        assert eq(a, [-44, 1, -55, 3, 4])

    def test_ravel(self):
        a = unp.array([[1, 2, 3],
                       [4, 5, 6]])
        assert eq(unp.ravel(a), [1, 2, 3, 4, 5, 6])

    def test_repeat(self):
        a = unp.array([1, 2, 3])
        assert eq(unp.repeat(a, 2), [1, 1, 2, 2, 3, 3])

    def test_reshape(self):
        a = unp.array([1, 2, 3, 4])
        assert eq(unp.reshape(a, (2, 2)), [[1, 2], [3, 4]])

    def test_round(self):
        a = unp.array([1.1234, 2.4567])
        assert eq(unp.round(a, 2), [1.12, 2.46])

    def test_squeeze(self):
        a = unp.array([[[0], [1], [2]]])
        assert eq(unp.squeeze(a), [0, 1, 2])

    def test_sum(self):
        a = unp.array([1, 2, 3])
        assert unp.sum(a) == 6

    def test_swapaxes(self):
        a = unp.array([[1, 2, 3]])
        b = unp.swapaxes(a, 0, 1)
        assert eq(b, [[1], [2], [3]])

    def test_transpose(self):
        a = unp.array([[1, 2, 3],
                       [4, 5, 6],
                       [7, 8, 9]])
        b = unp.transpose(a)
        assert eq(b, [[1, 4, 7],
                      [2, 5, 8],
                      [3, 6, 9]])
