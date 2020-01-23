import requests
from typing import List, Dict
from bit.wallet import Unspent

PARAM_TIMEOUT_SEC = 5

# Base URL being accessed
URL_MAINNET = "https://blockchain.info"
URL_TESTNET = "https://testnet.blockchain.info"


def get_unspent(address: str, testnet: bool = False) -> List[Unspent]:
    """Find all unspent transactions for a bitcoin address.

    This function uses a public service (e.g. blockchain.info)
    to fetch a list of unspent transactions.

    Args:
        address: String bitcoin address.

    Returns:
        List of unspent transactions that were found. Empty if
        none were found.
    """
    payload = {"active": address}
    url_base = URL_TESTNET if testnet else URL_MAINNET
    endpoint = f"{url_base}/unspent"
    r = requests.get(endpoint, params=payload, timeout=PARAM_TIMEOUT_SEC)
    r.raise_for_status()
    data = r.json()

    def to_unspent(utxo: Dict) -> Unspent:
        return Unspent(
            txid=utxo["tx_hash_big_endian"],
            txindex=utxo["tx_output_n"],
            script=utxo["script"],
            amount=utxo["value"],
            confirmations=utxo["confirmations"],
        )

    yield from (to_unspent(utxo) for utxo in data["unspent_outputs"])
