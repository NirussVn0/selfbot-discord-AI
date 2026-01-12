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
    is_captcha: bool = False
    won_amount: int = 0
    balance: int = 0
    confidence: float = 0.0


class OWOMessageParser:
    OWO_BOT_ID = 408785106942164992

    # Anchor to 'cowoncy' or emoji to avoid matching User IDs. 
    # Supports "won 500 cowoncy" AND "won :cowoncy: 500"
    # Handling full emoji ID: <a?:name:id>
    WIN_PATTERN = re.compile(
        r"won.*?(?:(\d[\d,]+)\s*(?:<a?:cowoncy\S*>|cowoncy|oo)|(?:<a?:cowoncy\S*>|cowoncy|oo)\s*[\*_]*\s*(\d[\d,]+))", 
        re.IGNORECASE | re.DOTALL
    )
    LOSS_PATTERN = re.compile(r"lost it all", re.IGNORECASE)
    COOLDOWN_PATTERN = re.compile(r"slow down|cooldown|wait|please wait", re.IGNORECASE)
    CAPTCHA_PATTERN = re.compile(r"renderer|captcha|verify|human|banned", re.IGNORECASE)
    BALANCE_PATTERN = re.compile(r"you currently have\s*([\d,]+)", re.IGNORECASE)

    @classmethod
    def parse_coinflip_result(cls, message: discord.Message) -> ParseResult:
        if message.author.id != cls.OWO_BOT_ID:
            return ParseResult(is_owo_response=False)

        # Check regular content
        content = message.content
        
        # Check embeds if content is empty or to supplement
        if message.embeds:
            for embed in message.embeds:
                if embed.description:
                    content += " " + embed.description
                if embed.title:
                    content += " " + embed.title

        # Debug logging to see what the bot actually sees
        # logger.debug(f"Parsing OWO message: {content!r}")

        if cls.CAPTCHA_PATTERN.search(content):
            return ParseResult(
                is_owo_response=True,
                is_captcha=True,
                confidence=1.0,
            )

        if cls.COOLDOWN_PATTERN.search(content):
            return ParseResult(
                is_owo_response=True,
                is_cooldown=True,
                confidence=0.9,
            )

        win_match = cls.WIN_PATTERN.search(content)
        if win_match:
            # Group 1 (Amount first) OR Group 2 (Currency first)
            amount_str = (win_match.group(1) or win_match.group(2)).replace(",", "")
            try:
                amount = int(amount_str)
                # Safety check: OWO wins shouldn't exceed reasonable limits (e.g., >1 trillion)
                # This prevents matching Snowflake IDs (~18 digits)
                if amount < 1_000_000_000_000:
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
