"""
Parser for fixed-format A2A booking messages.
"""

from __future__ import annotations

import re
from typing import Tuple


class BookingMessageParser:
    """
    Parses fixed-format user messages:
    - 'reservar sala=<id> inicio=<iso8601> fim=<iso8601> responsavel=<nome>'
    - 'escolha=<id>' or 'escolha=recusar'
    """

    @staticmethod
    def parse_booking_arguments(text: str) -> dict[str, str]:
        args: dict[str, str] = {}
        sala_match = re.search(r"sala=([^\s]+)", text)
        inicio_match = re.search(r"inicio=([^\s]+)", text)
        fim_match = re.search(r"fim=([^\s]+)", text)
        resp_match = re.search(r"responsavel=([^\s]+)", text)

        if sala_match:
            args["sala"] = sala_match.group(1)
        if inicio_match:
            args["inicio"] = inicio_match.group(1)
        if fim_match:
            args["fim"] = fim_match.group(1)
        if resp_match:
            args["responsavel"] = resp_match.group(1)

        return args

    @staticmethod
    def parse_choice(text: str) -> Tuple[str, str]:
        """
        Extracts choice from message.
        Returns tuple of (action, value):
          - ("decline", "recusar")
          - ("accept", "<sala_id>")
          - ("none", "")
        """
        match = re.search(r"escolha=([^\s]+)", text)
        if not match:
            return "none", ""
        val = match.group(1).strip()
        if val == "recusar":
            return "decline", val
        return "accept", val
