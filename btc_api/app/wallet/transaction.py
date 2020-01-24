from __future__ import annotations
import math
from typing import List
from dataclasses import dataclass, astuple
from fractions import Fraction
from bit.transaction import (
    TxIn,
    TxObj,
    construct_outputs,
    address_to_scriptpubkey,
    estimate_tx_fee,
)
from bit.constants import LOCK_TIME, VERSION_2
from bit.wallet import Unspent
from bit.utils import hex_to_bytes


@dataclass
class Output:
    """Class for keeping track of our transaction outputs."""

    address: str
    amount: int

    def __iter__(self):
        """Makes it unpackable."""

        yield from astuple(self)


@dataclass(frozen=True)
class TxContext:
    """Class representing context for the transaction."""

    address: str
    inputs: List[Unspent]
    outputs: List[Output]
    fee_kb: int
    change_address: str

    def copy_with_selected(self, inputs: List[Unspent]) -> TxContext:
        return TxContext(
            self.address,
            inputs,  # we change the inputs on new context
            self.outputs,
            self.fee_kb,
            self.change_address,
        )


def create_unsigned(inputs: List[Unspent], outputs: List[Output]) -> TxObj:
    """Creates an unsigned transaction object"""

    raw_outputs = construct_outputs(outputs)
    raw_inputs = [
        TxIn(
            script_sig=b"",  # empty scriptSig for new unsigned transaction.
            txid=hex_to_bytes(utxo.txid)[::-1],
            txindex=utxo.txindex.to_bytes(4, byteorder="little"),
            amount=utxo.amount.to_bytes(8, byteorder="little"),
        )
        for utxo in inputs
    ]
    return TxObj(VERSION_2, raw_inputs, raw_outputs, LOCK_TIME)


def address_to_scriptpubkey_size(address: str) -> int:
    """Calculates total size (in bytes) of P2PKH/P2SH scriptpubkey"""

    return len(address_to_scriptpubkey(address)) + 9


def estimate_tx_fee_kb(in_size, n_in, out_size, n_out, fee_kb) -> int:
    """Estimates transaction fee using satoshis per kilobyte"""

    fee_byte = Fraction(fee_kb, 1024)
    fee = estimate_tx_fee(in_size, n_in, out_size, n_out, fee_byte)
    return math.ceil(fee)
