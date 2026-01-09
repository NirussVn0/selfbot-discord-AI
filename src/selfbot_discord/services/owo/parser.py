from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord


@dataclass(slots=True)
class ParseResult:
    is_owo_response: bool
    is_win: bool = False
    is_loss: bool = False
    is_cooldown: bool = False
    won_amount: int = 0
    balance: int = 0
    confidence: float = 0.0


class OWOMessageParser:
    OWO_BOT_ID = 408785106942164992

    WIN_PATTERN = re.compile(r":head:.*?won.*?:cowoncy:\s*(\d[\d,]*)", re.IGNORECASE)
    LOSS_PATTERN = re.compile(r":tail:.*?lost it all.*?:c", re.IGNORECASE)
    COOLDOWN_PATTERN = re.compile(r"slow down|cooldown|wait", re.IGNORECASE)
    BALANCE_PATTERN = re.compile(r"cowoncy.*?(\d[\d,]*)", re.IGNORECASE)

    @classmethod
    def parse_coinflip_result(cls, message: discord.Message) -> ParseResult:
        if message.author.id != cls.OWO_BOT_ID:
            return ParseResult(is_owo_response=False)

        content = message.content.lower()

        win_match = cls.WIN_PATTERN.search(content)
        if win_match:
            amount_str = win_match.group(1).replace(",", "")
            try:
                amount = int(amount_str)
                return ParseResult(
                    is_owo_response=True,
                    is_win=True,
                    won_amount=amount,
                    confidence=1.0,
                )
            except ValueError:
                pass

        if cls.LOSS_PATTERN.search(content):
            return ParseResult(
                is_owo_response=True,
                is_loss=True,
                confidence=1.0,
            )

        if cls.COOLDOWN_PATTERN.search(content):
            return ParseResult(
                is_owo_response=True,
                is_cooldown=True,
                confidence=0.9,
            )

        return ParseResult(is_owo_response=False)

    @classmethod
    def parse_balance(cls, message: discord.Message) -> ParseResult:
        if message.author.id != cls.OWO_BOT_ID:
            return ParseResult(is_owo_response=False)

        content = message.content.lower()
        balance_match = cls.BALANCE_PATTERN.search(content)

        if balance_match:
            balance_str = balance_match.group(1).replace(",", "")
            try:
                balance = int(balance_str)
                return ParseResult(
                    is_owo_response=True,
                    balance=balance,
                    confidence=0.95,
                )
            except ValueError:
                pass

        return ParseResult(is_owo_response=False)
