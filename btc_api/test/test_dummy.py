import unittest

from app.payment import PaymentTxRequest, RANDOM_SEED


class TestSum(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")

    def test_sum_tuple(self):
        self.assertEqual(sum((1, 2, 3)), 6, "Should be 6")

    def test_seer(self):
        self.assertEqual(RANDOM_SEED, 1234, "Should be 1234")


if __name__ == "__main__":
    unittest.main()
