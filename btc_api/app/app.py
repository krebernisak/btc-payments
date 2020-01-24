from flask import Flask, escape, request, jsonify
from werkzeug.exceptions import HTTPException, InternalServerError
from app.errors import InvalidUsage, ErrorResponse, BAD_REQUEST, INTERNAL_SERVER_ERROR
from app.payment import (
    PaymentTxRequest,
    process_payment_tx_request,
    MIN_CONFIRMATIONS,
    MIN_RELAY_FEE,
)
from app.wallet.exceptions import InsufficientFunds

app = Flask(__name__)


def error_to_json_response(err: ErrorResponse):
    """Maps ErrorResponse to HTTP JSON response ."""

    response = jsonify(err.to_dict())
    response.status_code = err.status_code
    return response


@app.errorhandler(InvalidUsage)
def handle_user_exception(e):
    """Return JSON instead of HTML for InvalidUsage errors."""

    error = ErrorResponse(e.status_code, e.__class__.__name__, e.message, e.payload)
    return error_to_json_response(error)


@app.errorhandler(InsufficientFunds)
def handle_wallet_exception(e):
    """Return JSON instead of HTML for InsufficientFunds errors."""

    error = ErrorResponse(
        BAD_REQUEST,
        e.__class__.__name__,
        e.message,
        {"address": e.address, "balance": e.balance},
    )
    return error_to_json_response(error)


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
    return error_to_json_response(error)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""

    error = ErrorResponse(e.code, e.__class__.__name__, e.description)
    return error_to_json_response(error)


@app.route("/")
def hello():
    name = request.args.get("name", "Xapo")
    return f"Hello, {escape(name)}!"


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

    response = process_payment_tx_request(data)
    return jsonify(response.to_dict())


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
