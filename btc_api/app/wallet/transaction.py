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

# empty scriptSig for new unsigned transaction.
EMPTY_SCRIPT_SIG = b""
VALUE_SIZE = 8
VAR_INT_MIN_SIZE = 1
BYTES_IN_KB = 1024


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

    def copy(
        self, *, inputs: List[Unspent] = None, outputs: List[Output] = None
    ) -> TxContext:
        return TxContext(
            self.address,
            inputs if inputs is not None else self.inputs,
            outputs if outputs is not None else self.outputs,
            self.fee_kb,
            self.change_address,
        )


def create_unsigned(inputs: List[Unspent], outputs: List[Output]) -> TxObj:
    """Creates an unsigned transaction object"""

    raw_outputs = construct_outputs(outputs)
    raw_inputs = [
        TxIn(
            script_sig=EMPTY_SCRIPT_SIG,
            txid=serialize_txid(utxo.txid),
            txindex=serialize_txindex(utxo.txindex),
            amount=serialize_amount(utxo.amount),
        )
        for utxo in inputs
    ]
    return TxObj(VERSION_2, raw_inputs, raw_outputs, LOCK_TIME)


def serialize_txid(txid: str) -> bytes:
    """Serializes txid to bytes"""

    return hex_to_bytes(txid)[::-1]


def serialize_txindex(txindex: int) -> bytes:
    """Serializes txindex to bytes"""

    return txindex.to_bytes(4, byteorder="little")


def serialize_amount(amount: int) -> bytes:
    """Serializes amount to bytes"""

    return amount.to_bytes(8, byteorder="little")


def address_to_output_size(address: str) -> int:
    """Calculates total size (in bytes) of TxOut for address"""

    return VALUE_SIZE + VAR_INT_MIN_SIZE + len(address_to_scriptpubkey(address))


def estimate_tx_fee_kb(in_size, n_in, out_size, n_out, fee_kb) -> int:
    """Estimates transaction fee using satoshis per kilobyte"""

    fee_byte = Fraction(fee_kb, BYTES_IN_KB)
    fee = estimate_tx_fee(in_size, n_in, out_size, n_out, fee_byte)
    return math.ceil(fee)
