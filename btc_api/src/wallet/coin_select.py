import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple

from bit.wallet import Unspent

from wallet.transaction import (
    TxContext,
    Output,
    address_to_scriptpubkey_size,
    estimate_tx_fee_kb,
)
from wallet.exceptions import InsufficientFunds

DUST_THRESHOLD = 5430


@dataclass(frozen=True)
class SelectedCoins:
    """Class represents result of a successfull coin selection."""

    inputs: List[Unspent]
    outputs: List[Output]
    out_amount: int
    change_amount: int
    fee_amount: int


class UnspentCoinSelector(ABC):
    """
    The Strategy interface declares common interface for all supported coin
    select algorithms.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs.

        Returns a result of a successfull coin selection.
        """
        pass


class Greedy(UnspentCoinSelector):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using greedy algorithm
        until enough are selected from input list.

        Returns a result of a successfull coin selection.
        """

        outputs = context.outputs[:]

        n_out = len(outputs)
        out_amount = sum(out.amount for out in outputs)
        out_size = sum(address_to_scriptpubkey_size(out.address) for out in outputs)

        in_size = 0
        in_amount = 0
        change_amount = 0
        change_included = False

        for n_in, utxo in enumerate(context.inputs, 1):
            in_size += utxo.vsize
            fee = estimate_tx_fee_kb(in_size, n_in, out_size, n_out, context.fee_kb)

            in_amount += utxo.amount
            change_amount = in_amount - (out_amount + fee)
            change_amount = change_amount if change_amount >= DUST_THRESHOLD else 0
            fee = fee + change_amount if 0 > change_amount < DUST_THRESHOLD else fee

            if change_amount and not change_included:
                n_out += 1
                out_size += address_to_scriptpubkey_size(context.change_address)
                fee = estimate_tx_fee_kb(in_size, n_in, out_size, n_out, context.fee_kb)
                change_included = True

            if out_amount + fee + change_amount <= in_amount:
                break
            elif n_in == len(context.inputs):
                raise InsufficientFunds.forAmount(
                    context.address, in_amount, out_amount, fee
                )

        selected_inputs = context.inputs[:n_in]

        if change_amount:
            outputs.append(Output(context.change_address, change_amount))

        return SelectedCoins(selected_inputs, outputs, out_amount, change_amount, fee)


class GreedyMaxSecure(Greedy):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using oldest coins first.

        Returns a result of a successfull coin selection.
        """

        sorted_inputs = sorted(context.inputs, key=lambda utxo: -utxo.confirmations)
        return super().select(context.copy_with_selected(sorted_inputs))


class GreedyMaxCoins(Greedy):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using coins with min amount first.
        Try to spend MAX number of coins.

        Returns a result of a successfull coin selection.
        """

        sorted_inputs = sorted(context.inputs, key=lambda utxo: utxo.amount)
        return super().select(context.copy_with_selected(sorted_inputs))


class GreedyMinCoins(Greedy):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using coins with max amount first.
        Try to spend MIN number of coins.

        Returns a result of a successfull coin selection.
        """

        sorted_inputs = sorted(context.inputs, key=lambda utxo: -utxo.amount)
        return super().select(context.copy_with_selected(sorted_inputs))


class GreedyRandom(Greedy):
    def __init__(self, random):
        self.random = random

    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs on random.

        Returns a result of a successfull coin selection.
        """

        shuffled_copy = context.inputs[:]
        self.random.shuffle(shuffled_copy)
        return super().select(context.copy_with_selected(shuffled_copy))
