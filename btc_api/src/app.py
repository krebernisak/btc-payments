from flask import Flask, escape, request
from bitcoin_query import get_unspent

app = Flask(__name__)


@app.route("/")
def hello():
    name = request.args.get("name", "Xapo")
    return f"Hello, {escape(name)}!"


@app.route("/payment_transactions")
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

    Response body (dictionary):
        raw (string): The unsigned raw transaction
        inputs (array of dicts): The inputs used
        txid (string): The transaction id
        vout (int): The output number
        script_pub_key (string): The script pub key
        amount (int): The amount in SAT
    """
    name = request.args.get("name", "BTC")
    return f"Hello, {escape(name)}!"


def main():
    use_debugger = app.debug
    app.run(
        use_debugger=use_debugger,
        debug=app.debug,
        use_reloader=use_debugger,
        host="0.0.0.0",
    )


if __name__ == "__main__":
    main()
