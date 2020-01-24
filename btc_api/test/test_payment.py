import unittest

from app.errors import InvalidUsage
from app.payment import (
    coin_select_strategies,
    PaymentTxRequest,
    RANDOM_SEED,
    MIN_RELAY_FEE,
    DEFAULT_STRATEGY,
    MIN_CONFIRMATIONS,
)
from app.payment_errors import (
    EmptySourceAddress,
    InvalidSourceAddress,
    NetworkMismatchSourceAddress,
    NotSupportedSourceAddress,
    EmptyOutputs,
    InvalidOutputAddress,
    InvalidOutputAmount,
    NotSupportedOutputAddress,
    NetworkMismatchOutputAddress,
    InvalidStrategy,
    InvalidFee,
    InvalidMinConfirmations,
)
from app.wallet.coin_select import DUST_THRESHOLD

MAINNET_P2PKH = "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh"
MAINNET_P2SH = "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX"
MAINNET_BECH32 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
TESTNET_P2PKH = "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn"
TESTNET_P2SH = "2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc"
TESTNET_BECH32 = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"

val = DUST_THRESHOLD


class TestPaymentTxRequest(unittest.TestCase):

    # test source_address validation

    def test_source_address_empty(self):
        with self.assertRaises(EmptySourceAddress):
            PaymentTxRequest("", {}, 0)

    def test_source_address_invalid(self):
        with self.assertRaises(InvalidSourceAddress):
            PaymentTxRequest("12345", {}, 0)

    def test_source_address_invalid_2(self):
        with self.assertRaises(InvalidSourceAddress):
            PaymentTxRequest("abc", {}, 0)

    def test_source_address_net_mismatch(self):
        with self.assertRaises(NetworkMismatchSourceAddress):
            PaymentTxRequest(TESTNET_P2PKH, {}, 0)

    def test_source_address_net_mismatch_2(self):
        with self.assertRaises(NetworkMismatchSourceAddress):
            PaymentTxRequest(MAINNET_P2PKH, {}, 0, testnet=True)

    def test_source_address_not_supported(self):
        with self.assertRaises(NotSupportedSourceAddress):
            PaymentTxRequest(MAINNET_P2SH, {}, 0)

    def test_source_address_not_supported_2(self):
        with self.assertRaises(NotSupportedSourceAddress):
            PaymentTxRequest(TESTNET_P2SH, {}, 0, testnet=True)

    # test outputs validation

    def test_output_empty(self):
        with self.assertRaises(EmptyOutputs):
            PaymentTxRequest(TESTNET_P2PKH, {}, 0, testnet=True)

    def test_output_empty__2(self):
        with self.assertRaises(EmptyOutputs):
            PaymentTxRequest(MAINNET_P2PKH, {}, 0)

    def test_output_invalid(self):
        with self.assertRaises(InvalidOutputAddress):
            PaymentTxRequest(TESTNET_P2PKH, {"mipcBbFg": val}, 0, testnet=True)

    def test_output_invalid_2(self):
        with self.assertRaises(InvalidOutputAddress):
            PaymentTxRequest(MAINNET_P2PKH, {"1Po1oWkD": val}, 0)

    def test_output_not_supported(self):
        with self.assertRaises(NotSupportedOutputAddress):
            PaymentTxRequest(TESTNET_P2PKH, {TESTNET_BECH32: val}, 0, testnet=True)

    def test_output_not_supported_2(self):
        with self.assertRaises(NotSupportedOutputAddress):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_BECH32: val}, 0)

    def test_output_net_mismatch(self):
        with self.assertRaises(NetworkMismatchOutputAddress):
            PaymentTxRequest(TESTNET_P2PKH, {MAINNET_P2PKH: val}, 0, testnet=True)

    def test_output_net_mismatch_2(self):
        with self.assertRaises(NetworkMismatchOutputAddress):
            PaymentTxRequest(MAINNET_P2PKH, {TESTNET_P2PKH: val}, 0)

    def test_output_amount_invalid(self):
        with self.assertRaises(InvalidOutputAmount):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: 0}, 0)

    def test_output_amount_invalid_2(self):
        with self.assertRaises(InvalidOutputAmount):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: -1}, 0)

    def test_output_amount_invalid_3(self):
        with self.assertRaises(InvalidOutputAmount):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val - 10}, 0)

    # test fee_kb validation

    def test_fee_kb_invalid(self):
        with self.assertRaises(InvalidFee):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val}, 0)

    def test_fee_kb_invalid_2(self):
        with self.assertRaises(InvalidFee):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val}, "a")

    def test_fee_kb_invalid_3(self):
        with self.assertRaises(InvalidFee):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val}, -1)

    def test_fee_kb_invalid_4(self):
        with self.assertRaises(InvalidFee):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val}, 50)

    # test strategy validation

    def test_strategy_invalid(self):
        with self.assertRaises(InvalidStrategy):
            PaymentTxRequest(MAINNET_P2PKH, {MAINNET_P2PKH: val}, 1000, strategy="aaa")

    def test_strategy_invalid_2(self):
        with self.assertRaises(InvalidStrategy):
            PaymentTxRequest(
                MAINNET_P2PKH, {MAINNET_P2PKH: val}, "1000", strategy="greedy"
            )

    # test min_confirmation validation

    def test_min_confirmation_invalid(self):
        with self.assertRaises(InvalidMinConfirmations):
            PaymentTxRequest(
                MAINNET_P2PKH, {MAINNET_P2PKH: val}, 1000, min_confirmations="a",
            )

    def test_min_confirmation_invalid_2(self):
        with self.assertRaises(InvalidMinConfirmations):
            PaymentTxRequest(
                MAINNET_P2PKH, {MAINNET_P2PKH: val}, "1000", min_confirmations=-1,
            )

    # test happy path validation

    def test_valid_requests(self):
        strategy_options = list(coin_select_strategies.keys())
        cases = [
            (MAINNET_P2PKH, {MAINNET_P2PKH: val}),
            (MAINNET_P2PKH, {MAINNET_P2PKH: val}, 1000),
            (MAINNET_P2PKH, {MAINNET_P2PKH: val}, "1000"),
            (MAINNET_P2PKH, {MAINNET_P2PKH: val}, 1024),
            (MAINNET_P2PKH, {MAINNET_P2SH: val}, 1024),
            (MAINNET_P2PKH, {MAINNET_P2SH: val}, 1024),
        ]

        multi_output_main = {MAINNET_P2PKH: val, MAINNET_P2SH: val}
        multi_output_test = {TESTNET_P2PKH: val, TESTNET_P2SH: val}
        cases += [
            case
            for strategy in strategy_options
            for case in [
                (MAINNET_P2PKH, {MAINNET_P2PKH: val}, 1024, strategy),
                (MAINNET_P2PKH, {MAINNET_P2SH: val}, 1024, strategy),
                (MAINNET_P2PKH, multi_output_main, 1024, strategy),
                (TESTNET_P2PKH, {TESTNET_P2PKH: val}, 1024, strategy, 6, True,),
                (TESTNET_P2PKH, {TESTNET_P2SH: val}, 1024, strategy, 6, True,),
                (TESTNET_P2PKH, multi_output_test, 1024, strategy, 6, True,),
            ]
        ]

        for n, data in enumerate(cases, 1):
            with self.subTest(n=n):
                r = PaymentTxRequest(*data)
                self.assertIsNotNone(r)
                self.assertEqual(r.source_address, data[0])
                self.assertEqual(r.outputs, data[1])
                self.assertEqual(
                    r.fee_kb,
                    int(data[2])
                    if len(data) > 2 and data[2] is not None
                    else MIN_RELAY_FEE,
                )
                self.assertEqual(
                    r.strategy,
                    data[3]
                    if len(data) > 3 and data[3] is not None
                    else DEFAULT_STRATEGY,
                )
                self.assertEqual(
                    r.min_confirmations,
                    int(data[4])
                    if len(data) > 4 and data[4] is not None
                    else MIN_CONFIRMATIONS,
                )


if __name__ == "__main__":
    unittest.main()
