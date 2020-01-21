import requests
from typing import List, Dict
from bit.wallet import Unspent

PARAM_TIMEOUT_SEC = 5

# TODO: testnet
# Base URL being accessed
URL_BASE = "https://blockchain.info"
URL_UNSPENT = f"{URL_BASE}/unspent"


def get_unspent(address: str) -> List[Unspent]:
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
    r = requests.get(URL_UNSPENT, params=payload, timeout=PARAM_TIMEOUT_SEC)
    r.raise_for_status()
    data = r.json()

    def to_unspent(tx: Dict) -> Unspent:
        return Unspent(
            amount=tx["value"],
            confirmations=tx["confirmations"],
            script=tx["script"],
            txid=tx["tx_hash_big_endian"],
            txindex=tx["tx_output_n"],
        )

    yield from (to_unspent(tx) for tx in data["unspent_outputs"])
