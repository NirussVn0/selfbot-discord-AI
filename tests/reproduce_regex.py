
import re
import unittest
from dataclasses import dataclass

# Mock ParseResult for testing
@dataclass
class ParseResult:
    is_owo_response: bool
    is_win: bool = False
    is_loss: bool = False
    won_amount: int = 0
    confidence: float = 0.0

# Copy of the current logic from parser.py (to reproduce failure)
class OWOMessageParser:
    # Anchor to 'cowoncy' or emoji to avoid matching User IDs. 
    # Supports "won 500 cowoncy" AND "won :cowoncy: 500"
    # CURRENT BROKEN REGEX FROM CODEBASE
    # Note: I am intentionally using the one I suspect is broken
    WIN_PATTERN = re.compile(
        r"won.*?(?:(\d[\d,]+)\s*(?:<a?:cowoncy\S*>|cowoncy|oo)|(?:<a?:cowoncy\S*>|cowoncy|oo)\s*[\*_]*\s*(\d[\d,]+))", 
        re.IGNORECASE | re.DOTALL
    )

    @classmethod
    def parse(cls, content):
        win_match = cls.WIN_PATTERN.search(content)
        if win_match:
            amount_str = (win_match.group(1) or win_match.group(2)).replace(",", "")
            try:
                amount = int(amount_str)
                return ParseResult(True, is_win=True, won_amount=amount)
            except ValueError:
                return ParseResult(False)
        return ParseResult(False)

class TestOWOParser(unittest.TestCase):
    def test_currency_last(self):
        # Case 1: Amount then Currency (Standard)
        msg = "you won 500 cowoncy!!"
        result = OWOMessageParser.parse(msg)
        self.assertTrue(result.is_win)
        self.assertEqual(result.won_amount, 500)

    def test_currency_first_simple_emoji(self):
        # Case 2: Emoji literal (no ID) then Amount
        msg = "you won :cowoncy: 500!!"
        result = OWOMessageParser.parse(msg)
        # In discord :cowoncy: usually renders as the full ID, but let's test the simple case
        # The current regex expects <a?:cowoncy ... 
        # Actually :cowoncy: without <> is treated as text "cowoncy"?
        # "won :cowoncy: 500" -> regex matches "cowoncy" part?
        pass

    def test_currency_first_full_emoji(self):
        # Case 3: Full Discord Emoji ID then Amount (THE FAILURE CASE)
        msg = "**thd** spent **<:cowoncy:416043450337853441> 100** and chose **tails**\nThe coin spins... <:head:436677933977960478> and you won **<:cowoncy:416043450337853441> 200**!!"
        result = OWOMessageParser.parse(msg)
        print(f"\nTesting Full Emoji: Result={result}")
        self.assertTrue(result.is_win, "Failed to match Full Emoji ID format")
        self.assertEqual(result.won_amount, 200)

    def test_multiline(self):
        msg = "you won \n 1,000 cowoncy"
        result = OWOMessageParser.parse(msg)
        self.assertTrue(result.is_win)
        self.assertEqual(result.won_amount, 1000)

if __name__ == '__main__':
    unittest.main()
