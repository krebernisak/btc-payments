from app.errors import InvalidUsage, BAD_REQUEST

# source_address errors


class EmptySourceAddress(InvalidUsage):
    """Error when source address is empty."""

    def __init__(self):
        super().__init__("Please specify non-empty source address.", BAD_REQUEST)


class InvalidSourceAddress(InvalidUsage):
    """Error when source address is invalid."""

    def __init__(self, source_address, description):
        super().__init__(
            "Please specify valid source address.",
            BAD_REQUEST,
            payload={"source_address": source_address, "description": description},
        )


class NetworkMismatchSourceAddress(InvalidUsage):
    """Error when source address is from wrong network."""

    def __init__(self, source_address, source_net, requested_net):
        super().__init__(
            f"Cannot send from {source_net}net address {source_address} if using {requested_net}net.",
            BAD_REQUEST,
            payload={
                "requested_net": requested_net,
                "source_address": source_address,
                "source_net": source_net,
            },
        )


class NotSupportedSourceAddress(InvalidUsage):
    """Error when source address is not supported."""

    def __init__(self):
        super().__init__("Only P2PKH inputs are supported", BAD_REQUEST)


# outputs errors


class EmptyOutputs(InvalidUsage):
    """Error when outputs are empty."""

    def __init__(self):
        super().__init__("Please specify at least one output", BAD_REQUEST)


class NotSupportedOutputAddress(InvalidUsage):
    """Error when output address is not supported."""

    def __init__(self):
        super().__init__("Only P2PKH/P2SH outputs are supported", BAD_REQUEST)


class InvalidOutputAddress(InvalidUsage):
    """Error when output address is invalid."""

    def __init__(self, dest_address, description):
        super().__init__(
            "Please specify valid destination address.",
            BAD_REQUEST,
            payload={"dest_address": dest_address, "description": description},
        )


class NetworkMismatchOutputAddress(InvalidUsage):
    """Error when output address is from wrong network."""

    def __init__(
        self, source_address, source_net, dest_address, dest_net, requested_net
    ):
        super().__init__(
            f"Cannot send to {dest_net}net address {dest_address} when spending from a {source_net}net address {source_address}.",
            BAD_REQUEST,
            payload={
                "requested_net": requested_net,
                "source_address": source_address,
                "source_net": source_net,
                "dest_address": dest_address,
                "dest_net": dest_net,
            },
        )


class InvalidOutputAmount(InvalidUsage):
    """Error when output amount is invalid."""

    def __init__(self, amount, min_amount, description):
        super().__init__(
            f"Please specify valid output amount >= {min_amount} (minimum).",
            BAD_REQUEST,
            payload={"amount": amount, "description": description},
        )


# strategy errors


class InvalidStrategy(InvalidUsage):
    """Error when strategy is invalid."""

    def __init__(self, strategy, available_strategies):
        available_strategies_str = "|".join(available_strategies)
        super().__init__(
            f"Please specify one of [{available_strategies_str}] for strategy.",
            BAD_REQUEST,
            payload={"strategy": strategy},
        )


# fee_kb errors


class InvalidFee(InvalidUsage):
    """Error when fee_kb is invalid."""

    def __init__(self, fee_kb, min_fee_kb, description):
        super().__init__(
            f"Please specify valid number >= {min_fee_kb} (minimum) for fee_kb.",
            BAD_REQUEST,
            payload={"fee_kb": fee_kb, "description": description},
        )


# min_confirmations errors


class InvalidMinConfirmations(InvalidUsage):
    """Error when min_confirmations is invalid."""

    def __init__(self, min_confirmations, description):
        super().__init__(
            "Please specify valid number >= 0 for min_confirmations.",
            BAD_REQUEST,
            payload={
                "min_confirmations": min_confirmations,
                "description": description,
            },
        )
