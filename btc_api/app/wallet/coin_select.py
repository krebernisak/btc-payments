import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple
from functools import partial

from bit.wallet import Unspent

from app.wallet.transaction import (
    TxContext,
    Output,
    address_to_output_size,
    estimate_tx_fee_kb,
)
from app.wallet.exceptions import InsufficientFunds

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

        if not context.inputs:
            raise InsufficientFunds(context.address, 0)

        outputs = context.outputs[:]
        estimate_tx_fee = partial(estimate_tx_fee_kb, fee_kb=context.fee_kb)

        n_out = len(outputs)

        def change_included():
            return n_out == len(outputs) + 1

        out_amount = sum(out.amount for out in outputs)
        out_size = sum(address_to_output_size(out.address) for out in outputs)

        in_size = 0
        in_amount = 0
        change_amount = 0

        for n_in, utxo in enumerate(context.inputs, 1):
            in_size += utxo.vsize
            fee = estimate_tx_fee(in_size, n_in, out_size, n_out)

            in_amount += utxo.amount
            change_amount = max(0, in_amount - (out_amount + fee))
            if 0 < change_amount < DUST_THRESHOLD:
                fee += change_amount
                change_amount = 0
            elif change_amount >= DUST_THRESHOLD and not change_included():
                # Calculate new change_amount with fee including the change address output
                # and add it to tx if new estimate gives us change_amount >= DUST_THRESHOLD
                change_out_size = address_to_output_size(context.change_address)
                fee_with_change = estimate_tx_fee(
                    in_size, n_in, out_size + change_out_size, n_out + 1
                )
                change_amount_with_fee = in_amount - (out_amount + fee_with_change)
                if change_amount_with_fee < DUST_THRESHOLD:
                    fee += change_amount
                    change_amount = 0
                else:
                    n_out += 1
                    out_size += change_out_size
                    fee, change_amount = fee_with_change, change_amount_with_fee

            if out_amount + fee + change_amount <= in_amount:
                assert change_amount == 0 or change_amount >= DUST_THRESHOLD
                assert in_amount - (out_amount + fee + change_amount) == 0
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
        return super().select(context.copy(inputs=sorted_inputs))


class GreedyMaxCoins(Greedy):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using coins with min amount first.
        Try to spend MAX number of coins.

        Returns a result of a successfull coin selection.
        """

        sorted_inputs = sorted(context.inputs, key=lambda utxo: utxo.amount)
        return super().select(context.copy(inputs=sorted_inputs))


class GreedyMinCoins(Greedy):
    def select(self, context: TxContext) -> SelectedCoins:
        """
        Selects coins from unspent inputs using coins with max amount first.
        Try to spend MIN number of coins.

        Returns a result of a successfull coin selection.
        """

        sorted_inputs = sorted(context.inputs, key=lambda utxo: -utxo.amount)
        return super().select(context.copy(inputs=sorted_inputs))


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
        return super().select(context.copy(inputs=shuffled_copy))
