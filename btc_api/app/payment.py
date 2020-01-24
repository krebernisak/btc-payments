import random
from dataclasses import dataclass
from typing import List, Dict
from app.errors import InvalidUsage, BAD_REQUEST
from app.payment_errors import *
from app.wallet.query import get_unspent
from app.wallet.coin_select import (
    GreedyMaxSecure,
    GreedyMaxCoins,
    GreedyMinCoins,
    GreedyRandom,
    DUST_THRESHOLD,
)
from app.wallet.transaction import TxContext, Output, create_unsigned
from app.wallet.exceptions import (
    InsufficientFunds,
    EmptyUnspentTransactionOutputSet,
    NoConfirmedTransactionsFound,
)
from bit.wallet import Unspent
from bit.format import get_version

MIN_CONFIRMATIONS = 6
MIN_RELAY_FEE = 1000

RANDOM_SEED = 1234

random.seed(RANDOM_SEED)
coin_select_strategies = {
    "greedy_max_secure": GreedyMaxSecure(),
    "greedy_max_coins": GreedyMaxCoins(),
    "greedy_min_coins": GreedyMinCoins(),
    "greedy_random": GreedyRandom(random),
}

DEFAULT_STRATEGY = list(coin_select_strategies.keys())[0]

P2PKH_PREFIXES = {"1"}
P2SH_PREFIXES = {"3"}
P2PKH_TESTNET_PREFIXES = {"m", "n"}
P2SH_TESTNET_PREFIXES = {"2"}

supported_in_prefixes = P2PKH_PREFIXES | P2PKH_TESTNET_PREFIXES
supported_out_prefixes = supported_in_prefixes | P2SH_PREFIXES | P2SH_TESTNET_PREFIXES


@dataclass
class PaymentTxRequest:
    """Class representing request data for the /payment_transactions endpoint."""

    source_address: str
    outputs: Dict[str, int]
    fee_kb: int = MIN_RELAY_FEE
    strategy: str = DEFAULT_STRATEGY
    min_confirmations: int = MIN_CONFIRMATIONS
    testnet: bool = False

    def __post_init__(self):
        self.testnet = bool(self.testnet)
        self.requested_net = "test" if self.testnet else "main"

        self._validate_source_address()
        self._validate_outputs()
        self._validate_fee_kb()
        self._validate_strategy()
        self._validate_min_confirmations()

    def _validate_source_address(self):
        """Validates source_address attr."""

        if not self.source_address:
            raise EmptySourceAddress()

        try:
            self.source_net = get_version(self.source_address)
        except ValueError as err:
            raise InvalidSourceAddress(self.source_address, str(err))
        else:
            if self.source_net != self.requested_net:
                raise NetworkMismatchSourceAddress(
                    self.source_address, self.source_net, self.requested_net
                )

        if self.source_address[0] not in supported_in_prefixes:
            raise NotSupportedSourceAddress()

    def _validate_outputs(self):
        """Validates output addresses."""

        if not self.outputs:
            raise EmptyOutputs()

        # Sanity check: If spending from main-/testnet, then all output addresses must also be for main-/testnet.
        for dest in self.outputs.keys():
            if dest[0] not in supported_out_prefixes:
                raise NotSupportedOutputAddress()

            try:
                vs = get_version(dest)
            except ValueError as err:
                raise InvalidOutputAddress(dest, str(err))
            else:
                if vs and vs != self.requested_net:
                    raise NetworkMismatchOutputAddress(
                        self.source_address,
                        self.source_net,
                        dest,
                        vs,
                        self.requested_net,
                    )

            try:
                self.outputs[dest] = int(self.outputs[dest])
                if self.outputs[dest] < DUST_THRESHOLD:
                    raise ValueError("Output amount is lower that dust threshold.")
            except ValueError as err:
                raise InvalidOutputAmount(self.outputs[dest], DUST_THRESHOLD, str(err))

    def _validate_fee_kb(self):
        """Validates fee_kb attr."""

        try:
            self.fee_kb = int(self.fee_kb)
            if self.fee_kb < MIN_RELAY_FEE:
                raise ValueError("Fee per kb is too low.")
        except ValueError as err:
            raise InvalidFee(self.fee_kb, MIN_RELAY_FEE, str(err))

    def _validate_strategy(self):
        """Validates strategy attr."""

        if self.strategy not in coin_select_strategies.keys():
            raise InvalidStrategy(self.strategy, coin_select_strategies.keys())

    def _validate_min_confirmations(self):
        """Validates min_confirmations attr."""

        try:
            self.min_confirmations = int(self.min_confirmations)
            if self.min_confirmations < 0:
                raise ValueError("Number of confirmations can not be < 0.")
        except ValueError as err:
            raise InvalidMinConfirmations(self.min_confirmations, str(err))


@dataclass
class PaymentTxResponse:
    """Class representing response data for the /payment_transactions endpoint."""

    raw: str
    inputs: List[Unspent]

    def to_dict(self):
        return {
            "raw": self.raw,
            "inputs": [
                {
                    "txid": utxo.txid,
                    "vout": utxo.txindex,
                    "script_pub_key": utxo.script,
                    "amount": utxo.amount,
                }
                for utxo in self.inputs
            ],
        }


def process_payment_tx_request(request: PaymentTxRequest) -> PaymentTxResponse:
    """Uses request data to create a raw unsigned transaction response."""

    address = request.source_address
    change_address = address

    utxos = list(get_unspent(address, testnet=request.testnet))
    if not utxos:
        raise EmptyUnspentTransactionOutputSet(address)

    confirmed = [u for u in utxos if int(u.confirmations) >= request.min_confirmations]
    if not confirmed:
        raise NoConfirmedTransactionsFound(address, request.min_confirmations)

    outputs = [Output(addr, int(amount)) for addr, amount in request.outputs.items()]
    context = TxContext(address, confirmed, outputs, request.fee_kb, change_address)

    strategy = coin_select_strategies[request.strategy]
    selected_coins = strategy.select(context)

    tx = create_unsigned(selected_coins.inputs, selected_coins.outputs)

    return PaymentTxResponse(tx.to_hex(), selected_coins.inputs)
