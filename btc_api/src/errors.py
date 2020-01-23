from dataclasses import dataclass, asdict
from typing import Dict, Any
from flask import jsonify

BAD_REQUEST = 400
INTERNAL_SERVER_ERROR = 500


class InvalidUsage(Exception):
    """Exception representing invalid usage of the API service."""

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload


@dataclass
class ErrorResponse:
    """Class representing error response data for the API service."""

    status_code: str
    name: str
    message: str
    details: Dict[str, Any] = None

    def to_json_response(self):
        response = jsonify(asdict(self))
        response.status_code = self.status_code
        return response
