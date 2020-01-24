import unittest

from bit.wallet import Unspent
from app.wallet.exceptions import InsufficientFunds
from app.wallet.transaction import TxContext, Output
from app.wallet.coin_select import (
    Greedy,
    GreedyMaxSecure,
    GreedyMaxCoins,
    GreedyMinCoins,
    GreedyRandom,
    DUST_THRESHOLD,
)


class TestUnspentCoinSelector(unittest.TestCase):
    def test_empty_context(self):
        ctx = TxContext("", [], [], 0, "")
        strategy = Greedy()
        with self.assertRaises(InsufficientFunds):
            strategy.select(ctx)


if __name__ == "__main__":
    unittest.main()
