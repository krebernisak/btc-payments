import unittest

from bit.wallet import Unspent
from app.wallet.transaction import (
    TxContext,
    Output,
    address_to_output_size,
    estimate_tx_fee_kb,
    serialize_txid,
    serialize_txindex,
    serialize_amount,
    create_unsigned,
)


HEX_TX_ID = "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04"
BYTES_TX_ID = b"\x04\xdc\xc4Y\xf4\xd7\xf9Y\x14;\xef\x19\xe2\xf0\xfd\xb2\xad%\xe3\xd9\xaa'\xb8\x89B\xf0\xe7x\x84\r\xc7-"

MAINNET_P2PKH = "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh"
MAINNET_P2SH = "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX"
TESTNET_P2PKH = "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn"
TESTNET_P2SH = "2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc"

P2PKH_OUT_SIZE = 34
P2SH_OUT_SIZE = 32


class TestTransaction(unittest.TestCase):
    def test_serialize_txid(self):
        self.assertEqual(serialize_txid(HEX_TX_ID), BYTES_TX_ID)

    def test_serialize_txindex(self):
        self.assertEqual(serialize_txindex(0), b"\x00\x00\x00\x00")

    def test_serialize_txindex_2(self):
        self.assertEqual(serialize_txindex(320), b"@\x01\x00\x00")

    def test_serialize_amount(self):
        self.assertEqual(serialize_amount(10000), b"\x10'\x00\x00\x00\x00\x00\x00")

    def test_serialize_amount_2(self):
        self.assertEqual(serialize_amount(256), b"\x00\x01\x00\x00\x00\x00\x00\x00")

    def test_serialize_amount_3(self):
        self.assertEqual(serialize_amount(1024), b"\x00\x04\x00\x00\x00\x00\x00\x00")

    def test_p2pkh_output_size(self):
        self.assertEqual(address_to_output_size(MAINNET_P2PKH), P2PKH_OUT_SIZE)
        self.assertEqual(address_to_output_size(TESTNET_P2PKH), P2PKH_OUT_SIZE)

    def test_p2sh_output_size(self):
        self.assertEqual(address_to_output_size(MAINNET_P2SH), P2SH_OUT_SIZE)
        self.assertEqual(address_to_output_size(TESTNET_P2SH), P2SH_OUT_SIZE)

    def test_create_unsigned(self):
        inputs = [
            Unspent(**utxo)
            for utxo in [
                {
                    "amount": 152730,
                    "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                    "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                    "txindex": 319,
                    "confirmations": 6,
                },
                {
                    "amount": 102730,
                    "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                    "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                    "txindex": 63,
                    "confirmations": 6,
                },
            ]
        ]
        outputs = [
            Output(addr, amount)
            for addr, amount in {
                "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 10000,
                "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000,
            }.items()
        ]

        raw = (
            "020000000204dcc459f4d7f959143bef19e2f0fdb2ad25e3d9aa27b88942f0e778840d"
            "c72d3f01000000ffffffff04dcc459f4d7f959143bef19e2f0fdb2ad25e3d9aa27b889"
            "42f0e778840dc72d3f00000000ffffffff02102700000000000017a9148f55563b9a19"
            "f321c211e9b9f38cdf686ea0784587204e0000000000001976a91447376c6f537d6217"
            "7a2c41c4ca9b45829ab9908388ac00000000"
        )

        tx = create_unsigned(inputs, outputs)
        self.assertEqual(tx.to_hex(), raw)

    def test_create_unsigned_2(self):
        inputs = [
            Unspent(**utxo)
            for utxo in [
                {
                    "amount": 152730,
                    "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                    "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                    "txindex": 319,
                    "confirmations": 6,
                },
                {
                    "amount": 102730,
                    "script": "76a914fa0692278afe508514b5ffee8fe5e97732ce066988ac",
                    "txid": "2dc70d8478e7f04289b827aad9e325adb2fdf0e219ef3b1459f9d7f459c4dc04",
                    "txindex": 63,
                    "confirmations": 6,
                },
            ]
        ]
        outputs = [
            Output(addr, amount)
            for addr, amount in {
                "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 10000,
                "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000,
                "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh": 225054,  # change addr
            }.items()
        ]

        raw = (
            "020000000204dcc459f4d7f959143bef19e2f0fdb2ad25e3d9aa27b88942f0e778840d"
            "c72d3f01000000ffffffff04dcc459f4d7f959143bef19e2f0fdb2ad25e3d9aa27b889"
            "42f0e778840dc72d3f00000000ffffffff03102700000000000017a9148f55563b9a19"
            "f321c211e9b9f38cdf686ea0784587204e0000000000001976a91447376c6f537d6217"
            "7a2c41c4ca9b45829ab9908388ac1e6f0300000000001976a914fa0692278afe508514"
            "b5ffee8fe5e97732ce066988ac00000000"
        )

        tx = create_unsigned(inputs, outputs)
        self.assertEqual(tx.to_hex(), raw)


if __name__ == "__main__":
    unittest.main()
