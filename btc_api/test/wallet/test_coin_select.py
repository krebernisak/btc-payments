import unittest
import random
from functools import partial

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
    fee_kb=1024,
    change_address="1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
)

TEST_TX_2_IN_1_OUT_FEE = 338
TEST_TX_SUM_INPUTS = sum(utxo.amount for utxo in TEST_TX_CONTEXT.inputs)
TEST_TX_NO_CHANGE_AMOUNT = TEST_TX_SUM_INPUTS - TEST_TX_2_IN_1_OUT_FEE

P2PKH_OUT_SIZE = 34


class TestUnspentCoinSelector(unittest.TestCase):
    def test_empty_context(self):
        ctx = TxContext("", [], [], 0, "")
        strategy = Greedy()
        with self.assertRaises(InsufficientFunds):
            strategy.select(ctx)

    def test_insufficient_funds(self):
        ctx = TEST_TX_CONTEXT.copy(inputs=[TEST_TX_CONTEXT.inputs[1]])
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

    def _test_change(self, out_amount, n_out=1, change_amount=0, fee_amount=0):
        address = TEST_TX_CONTEXT.outputs[0].address
        ctx = TEST_TX_CONTEXT.copy(outputs=[Output(address, out_amount)])
        cases = [
            Greedy(),
            GreedyMaxSecure(),
            GreedyMaxCoins(),
            GreedyMinCoins(),
            GreedyRandom(random),
        ]

        for n, strategy in enumerate(cases, 1):
            with self.subTest(n=n):
                coins = strategy.select(ctx)
                self.assertEqual(len(coins.inputs), len(TEST_TX_CONTEXT.inputs))
                self.assertEqual(len(coins.outputs), n_out)
                self.assertEqual(coins.change_amount, change_amount)
                self.assertEqual(coins.out_amount, out_amount)
                sum_inputs_amount = sum(utxo.amount for utxo in ctx.inputs)
                change_and_fee = coins.change_amount + coins.fee_amount
                self.assertEqual(coins.out_amount + change_and_fee, sum_inputs_amount)
                self.assertEqual(out_amount + change_and_fee, sum_inputs_amount)
                self.assertEqual(coins.fee_amount, fee_amount)

    def test_change_no_change(self):
        self._test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT,
            n_out=1,
            change_amount=0,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE,
        )

    def test_change_no_change_under_dust_threshold(self):
        test_change = partial(self._test_change, n_out=1, change_amount=0,)

        test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - 1,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + 1,
        )
        test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - DUST_THRESHOLD // 10,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + DUST_THRESHOLD // 10,
        )
        test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - DUST_THRESHOLD // 3,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + DUST_THRESHOLD // 3,
        )
        test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - DUST_THRESHOLD // 2,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + DUST_THRESHOLD // 2,
        )
        test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - DUST_THRESHOLD,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + DUST_THRESHOLD,
        )

    def test_change_at_dust_threshold(self):
        self._test_change(
            out_amount=TEST_TX_NO_CHANGE_AMOUNT - (DUST_THRESHOLD + P2PKH_OUT_SIZE),
            n_out=2,
            change_amount=DUST_THRESHOLD,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + P2PKH_OUT_SIZE,
        )

    def test_change_over_dust_threshold(self):
        out_no_change_amount = TEST_TX_NO_CHANGE_AMOUNT
        test_change = partial(
            self._test_change,
            n_out=2,
            fee_amount=TEST_TX_2_IN_1_OUT_FEE + P2PKH_OUT_SIZE,
        )

        test_change(
            out_amount=out_no_change_amount - (DUST_THRESHOLD + P2PKH_OUT_SIZE + 1),
            change_amount=DUST_THRESHOLD + 1,
        )
        test_change(
            out_amount=out_no_change_amount - (DUST_THRESHOLD + P2PKH_OUT_SIZE + 79),
            change_amount=DUST_THRESHOLD + 79,
        )
        test_change(
            out_amount=out_no_change_amount - (DUST_THRESHOLD + P2PKH_OUT_SIZE + 1337),
            change_amount=DUST_THRESHOLD + 1337,
        )


if __name__ == "__main__":
    unittest.main()
