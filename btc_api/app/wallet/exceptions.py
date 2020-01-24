class WalletError(Exception):
    """Base Exception raised for all wallet errors."""

    pass


class InsufficientFunds(WalletError):
    """Error raised when address has insufficient funds to make a transaction.

    Attributes:
        address: input address for which the error occurred
        balance: current balance for the address
        message: explanation of the error
    """

    def __init__(self, address, balance=0):
        super().__init__()
        self.address = address
        self.balance = balance
        self.message = f"Insufficient funds for address {address}"

    @classmethod
    def forAmount(cls, address, balance, out_amount, fee):
        ex = cls(address, balance)
        total = out_amount + fee
        ex.message = f"Balance {balance} is less than {total} (including {fee} fee)"
        return ex

    def __str__(self):
        return self.message


class EmptyUnspentTransactionOutputSet(InsufficientFunds):
    """Error raised when address has an empty UTXO set.

    Attributes:
        address: input address for which the error occurred
        balance: current balance for the address
        message: explanation of the error
    """

    def __init__(self, address):
        super().__init__(address)
        self.message = f"No unspent transactions were found for address {address})"


class NoConfirmedTransactionsFound(InsufficientFunds):
    """Error raised when address has no confirmed unspent transactions to use.

    Attributes:
        address: input address for which the error occurred
        balance: current balance for the address
        message: explanation of the error
    """

    def __init__(self, address, min_confirmations):
        super().__init__(address)
        self.message = f"No confirmed unspent transactions were found for address {address} (asking for min: {min_confirmations})"
