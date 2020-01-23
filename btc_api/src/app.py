import random
from dataclasses import dataclass
from typing import List, Dict
from flask import Flask, escape, request, jsonify
from werkzeug.exceptions import HTTPException, InternalServerError
from errors import InvalidUsage, ErrorResponse, BAD_REQUEST, INTERNAL_SERVER_ERROR
from wallet.query import get_unspent
from wallet.coin_select import (
    GreedyMaxSecure,
    GreedyMaxCoins,
    GreedyMinCoins,
    GreedyRandom,
)
from wallet.transaction import TxContext, Output, create_unsigned
from wallet.exceptions import (
    InsufficientFunds,
    EmptyUnspentTransactionOutputSet,
    NoConfirmedTransactionsFound,
)
from bit.wallet import Unspent
from bit.format import get_version

app = Flask(__name__)


MIN_CONFIRMATIONS = 6
MIN_RELAY_FEE = 1000

RANDOM_SEED = 1234


@app.errorhandler(InvalidUsage)
def handle_user_exception(e):
    """Return JSON instead of HTML for InvalidUsage errors."""

    error = ErrorResponse(e.status_code, e.__class__.__name__, e.message, e.payload)
    return error.to_json_response()


@app.errorhandler(InsufficientFunds)
def handle_wallet_exception(e):
    """Return JSON instead of HTML for InsufficientFunds errors."""

    error = ErrorResponse(
        BAD_REQUEST,
        e.__class__.__name__,
        e.message,
        {"address": e.address, "balance": e.balance},
    )
    return error.to_json_response()


@app.errorhandler(InternalServerError)
def handle_500(e):
    """Return JSON instead of HTML for InternalServerError."""

    # if original is None, e represents direct 500 error, such as abort(500)
    # else e represents wrapped unhandled error
    original = getattr(e, "original_exception", None)

    error = ErrorResponse(
        INTERNAL_SERVER_ERROR,
        e.__class__.__name__ if original is None else original.__class__.__name__,
        e.description,
        None if not app.debug or not original else {"original": repr(original)},
    )
    return error.to_json_response()


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""

    error = ErrorResponse(e.code, e.__class__.__name__, e.description)
    return error.to_json_response()


@app.route("/")
def hello():
    name = request.args.get("name", "Xapo")
    return f"Hello, {escape(name)}!"


random.seed(RANDOM_SEED)
coin_select_strategies = {
    "greedy_max_secure": GreedyMaxSecure(),
    "greedy_max_coins": GreedyMaxCoins(),
    "greedy_min_coins": GreedyMinCoins(),
    "greedy_random": GreedyRandom(random),
}
available_strategies_str = "|".join(coin_select_strategies.keys())

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
    fee_kb: int
    strategy: str = "greedy_random"
    min_confirmations: int = MIN_CONFIRMATIONS
    testnet: bool = False

    def __post_init__(self):
        self.testnet = bool(self.testnet)
        self.requested_net = "test" if self.testnet else "main"

        self._validate_source_address()
        self._validate_outputs()
        self._validate_strategy()
        self._validate_fee_kb()
        self._validate_min_confirmations()

    def _validate_source_address(self):
        """Validates source_address attr."""

        if not self.source_address:
            raise InvalidUsage("Please specify non-empty source address", BAD_REQUEST)

        try:
            self.source_net = get_version(self.source_address)
        except ValueError as err:
            raise InvalidUsage(
                "Please specify valid source address.",
                BAD_REQUEST,
                payload={
                    "source_address": self.source_address,
                    "description": str(err),
                },
            )
        else:
            if self.source_net != self.requested_net:
                raise InvalidUsage(
                    f"Cannot send from {self.source_net}net address {self.source_address} if using {self.requested_net}net.",
                    BAD_REQUEST,
                    payload={
                        "requested_net": self.requested_net,
                        "source_address": self.source_address,
                        "source_net": self.source_net,
                    },
                )

        if self.source_address[0] not in supported_in_prefixes:
            raise InvalidUsage("Only P2PKH inputs are supported", BAD_REQUEST)

    def _validate_outputs(self):
        """Validates output addresses."""

        if not self.outputs:
            raise InvalidUsage("Please specify at least one output", BAD_REQUEST)

        # Sanity check: If spending from main-/testnet, then all output addresses must also be for main-/testnet.
        for dest in self.outputs.keys():
            if dest[0] not in supported_out_prefixes:
                raise InvalidUsage("Only P2PKH/P2SH outputs are supported", BAD_REQUEST)

            try:
                vs = get_version(dest)
            except ValueError as err:
                raise InvalidUsage(
                    "Please specify valid destination address.",
                    BAD_REQUEST,
                    payload={"dest_address": dest, "description": str(err)},
                )
            else:
                if vs and vs != self.requested_net:
                    raise InvalidUsage(
                        f"Cannot send to {vs}net address {dest} when spending from a {self.source_net}net address {self.source_address}.",
                        BAD_REQUEST,
                        payload={
                            "requested_net": self.requested_net,
                            "source_address": self.source_address,
                            "source_net": self.source_net,
                            "dest_address": dest,
                            "dest_net": vs,
                        },
                    )

    def _validate_strategy(self):
        """Validates strategy attr."""

        if self.strategy not in coin_select_strategies.keys():
            raise InvalidUsage(
                f"Please specify one of [{available_strategies_str}] for strategy.",
                BAD_REQUEST,
                payload={"strategy": self.strategy},
            )

    def _validate_fee_kb(self):
        """Validates fee_kb attr."""

        try:
            self.fee_kb = int(self.fee_kb)
            if self.fee_kb < MIN_RELAY_FEE:
                raise ValueError("Fee per kb is too low.")
        except ValueError as err:
            raise InvalidUsage(
                f"Please specify valid number >= {MIN_RELAY_FEE} (minimum) for fee_kb.",
                BAD_REQUEST,
                payload={"fee_kb": self.fee_kb, "description": str(err)},
            )

    def _validate_min_confirmations(self):
        """Validates min_confirmations attr."""

        try:
            self.min_confirmations = int(self.min_confirmations)
            if self.min_confirmations < 0:
                raise ValueError("Number of confirmations can not be < 0.")
        except ValueError as err:
            raise InvalidUsage(
                "Please specify valid number >= 0 for min_confirmations.",
                BAD_REQUEST,
                payload={
                    "min_confirmations": self.min_confirmations,
                    "description": str(err),
                },
            )


@dataclass
class PaymentTxResponse:
    """Class representing response data for the /payment_transactions endpoint."""

    raw: str
    inputs: List[Unspent]

    def to_json_response(self):
        return jsonify(
            {
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
        )


@app.route("/payment_transactions", methods=["POST"])
def payment_transactions():
    """
    This endpoint will be used to create a raw transaction that spends from a P2PKH
    address and that supports paying to multiple addresses (either P2PKH or P2SH).

    The endpoint should return a transaction that spends from the source address and
    that pays to the output addresses. An extra output for change should be included
    in the resulting transaction if the change is > 5430 SAT.

    URL: /payment_transactions
    Method: POST
    Request body (dictionary):
        source_address (string): The address to spend from
        outputs (dictionary): A dictionary that maps addresses to amounts (in SAT)
        fee_kb (int): The fee per kb in SAT
        strategy (str): One of [greedy_max_secure|greedy_max_coins|greedy_min_coins|greedy_random]
        min_confirmations (int): Min number of confirmations required to use UTXO as input (default 6)
        testnet (int): Is this a testnet transaction (default False)

    Response body (dictionary):
        raw (string): The unsigned raw transaction
        inputs (array of dicts): The inputs used
            txid (string): The transaction id
            vout (int): The output number
            script_pub_key (string): The script pub key
            amount (int): The amount in SAT
    """
    if not request.is_json:
        raise InvalidUsage(
            "Check if the mimetype indicates JSON data, either application/json or application/*+json.",
            BAD_REQUEST,
        )

    data_json = request.get_json()
    data = PaymentTxRequest(
        data_json.get("source_address", ""),
        data_json.get("outputs", ""),
        data_json.get("fee_kb", MIN_RELAY_FEE),
        data_json.get("strategy", "greedy_random"),
        data_json.get("min_confirmations", MIN_CONFIRMATIONS),
        data_json.get("testnet", False),
    )

    address = data.source_address
    change_address = address

    utxos = list(get_unspent(address, testnet=data.testnet))
    if not utxos:
        raise EmptyUnspentTransactionOutputSet(address)

    confirmed = [u for u in utxos if int(u.confirmations) >= data.min_confirmations]
    if not confirmed:
        raise NoConfirmedTransactionsFound(address, data.min_confirmations)

    outputs = [Output(addr, int(amount)) for addr, amount in data.outputs.items()]
    context = TxContext(address, confirmed, outputs, data.fee_kb, change_address)

    strategy = coin_select_strategies[data.strategy]
    selected_coins = strategy.select(context)

    tx = create_unsigned(selected_coins.inputs, selected_coins.outputs)

    response = PaymentTxResponse(tx.to_hex(), selected_coins.inputs)
    return response.to_json_response()


def app_run():
    use_debugger = app.debug
    use_reloader = app.debug
    app.run(
        use_debugger=use_debugger,
        debug=app.debug,
        use_reloader=use_reloader,
        host="0.0.0.0",
    )


if __name__ == "__main__":
    app_run()
