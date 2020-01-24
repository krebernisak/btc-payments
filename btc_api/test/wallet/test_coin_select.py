import unittest
import random

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

TEST_TX_CONTEXT = TxContext(
    address="1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
    inputs=[
        Unspent(**utxo)
        for utxo in [
            {
                "amount": 35273,
                "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                "txindex": 319,
                "confirmations": 6,
            },
            {
                "amount": 10273,
                "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                "txindex": 63,
                "confirmations": 9,
            },
        ]
    ],
    outputs=[
        Output(addr, amount)
        for addr, amount in {
            "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 10000,
            "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000,
        }.items()
    ],
    fee_kb=1000,
    change_address="1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
)


class TestUnspentCoinSelector(unittest.TestCase):
    def test_empty_context(self):
        ctx = TxContext("", [], [], 0, "")
        strategy = Greedy()
        with self.assertRaises(InsufficientFunds):
            strategy.select(ctx)

    def test_insufficient_funds(self):
        ctx = TEST_TX_CONTEXT.copy_with_selected([TEST_TX_CONTEXT.inputs[1]])
        cases = [
            Greedy(),
            GreedyMaxSecure(),
            GreedyMaxCoins(),
            GreedyMinCoins(),
            GreedyRandom(random),
        ]

        for n, strategy in enumerate(cases, 1):
            with self.subTest(n=n):
                with self.assertRaises(InsufficientFunds):
                    strategy.select(ctx)

    def test_strategies(self):
        random.seed(1234)
        cases = [
            (Greedy(), 1),
            (GreedyMaxSecure(), 2),
            (GreedyMaxCoins(), 2),
            (GreedyMinCoins(), 1),
            (GreedyRandom(random), 1),
            (GreedyRandom(random), 2),
        ]

        for n, data in enumerate(cases, 1):
            with self.subTest(n=n):
                ctx = TEST_TX_CONTEXT
                strategy = data[0]
                coins = strategy.select(ctx)
                self.assertEqual(len(coins.inputs), data[1])
                self.assertEqual(coins.out_amount, sum(a for _, a in ctx.outputs))


if __name__ == "__main__":
    unittest.main()
