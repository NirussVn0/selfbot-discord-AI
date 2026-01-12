from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from selfbot_discord.services.owo.models import BettingSide, StrategyFlag


class OWOUsageError(Exception):
    """Exception raised for invalid CLI arguments."""


@dataclass
class StartParams:
    amount: int
    active_flags: set[StrategyFlag] = field(default_factory=set)
    static_multiplier: float = 3.0
    betting_side: BettingSide = BettingSide.RANDOM


@dataclass
class CLIResult:
    action: Literal["start", "stop", "info", "reset", "clear", "usage"]
    start_params: StartParams | None = None
    message: str | None = None


class OWOArgParser:
    @staticmethod
    def parse(args: tuple[str, ...]) -> CLIResult:
        if not args:
            return CLIResult(action="usage")

        # Legacy check
        is_new_format = any(arg.startswith("-") for arg in args)
        
        if not is_new_format:
            cmd = args[0].lower()
            if cmd in ("stop", "s"):
                return CLIResult(action="stop")
            if cmd in ("info", "i"):
                return CLIResult(action="info")
            if cmd in ("reset",):
                return CLIResult(action="reset")
            if cmd.isdigit():
                return CLIResult(
                    action="start",
                    start_params=StartParams(amount=int(cmd))
                )
            return CLIResult(action="usage")
        
        action = "start"
        base_bet: int | None = None
        
        active_flags = set()
        static_multiplier: float = 3.0
        betting_side = BettingSide.RANDOM
        
        i = 0
        while i < len(args):
            arg = args[i].lower()
            
            # Action Flags
            if arg in ("-s", "-stop", "stop"):
                return CLIResult(action="stop")
            if arg in ("-i", "-info", "info"):
                return CLIResult(action="info") 
            if arg in ("-reset", "--reset"):
                return CLIResult(action="reset")
            if arg in ("-clear", "--clear"):
                return CLIResult(action="clear")
                
            # Parameter Flags
            elif arg in ("-b", "-bet"):
                if i + 1 >= len(args):
                    raise OWOUsageError("Missing amount for `-b` flag.")
                try:
                    base_bet = int(args[i+1])
                    i += 1
                except ValueError:
                    raise OWOUsageError(f"Invalid bet amount: {args[i+1]}")
            
            elif arg in ("-e", "-mode"):
                if i + 1 >= len(args):
                    raise OWOUsageError("Missing value for `-e` flag.")
                val = args[i+1].lower()
                i += 1
                
                mult, flags = self._parse_strategy_input(val)
                if mult is not None:
                    static_multiplier = mult
                active_flags.update(flags)

            elif arg in ("-side", "--side", "-sd"):
                if i + 1 >= len(args):
                    raise OWOUsageError("Missing value for `-side` flag.")
                side_val = args[i+1].lower()
                i += 1

                if side_val in ("h", "head", "heads"):
                    betting_side = BettingSide.HEADS
                elif side_val in ("t", "tail", "tails"):
                    betting_side = BettingSide.TAILS
                elif side_val in ("r", "rand", "random"):
                     betting_side = BettingSide.RANDOM
                else:
                     raise OWOUsageError(f"Invalid side: {side_val}. Use h, t, or r.")
            
            i += 1

        if base_bet is None:
            if action == "start":
                return CLIResult(action="usage")
        
        return CLIResult(
            action="start",
            start_params=StartParams(
                amount=base_bet,
                active_flags=active_flags,
                static_multiplier=static_multiplier,
                betting_side=betting_side
            )
        )

    @staticmethod
    def _parse_strategy_input(val: str) -> tuple[float | None, set[StrategyFlag]]:
        """Parses composite strategy string (e.g. 'x2-safe-random') -> (multiplier, flags)."""
        flags = set()
        multiplier: float | None = None
        
        if val == "auto":
            flags.add(StrategyFlag.AUTO_MULTIPLIER)
            return multiplier, flags

        # 1. Extract Number if present (e.g., x2.5 or 2.5)
        multiplier_match = re.match(r"^x?(\d*\.?\d+)", val)
        remaining = val
        
        if multiplier_match:
            num_str = multiplier_match.group(1)
            try:
                multiplier = float(num_str)
            except ValueError:
                raise OWOUsageError(f"Invalid multiplier number: {num_str}")
            remaining = val[multiplier_match.end():]
        elif not any(x in val for x in ["safe", "maintain", "random"]):
             # If no number AND no keywords match, defaulting might be dangerous or intended.
             # Logic implies if only mode given, mult defaults to None (preserved old val)
             # But if user types just logic flags, we return None for mult.
             pass

        if not multiplier and not remaining.strip("-"):
             # e.g., user entered just "x2" -> valid
             pass

        # 2. Parse Valid Strategy Keywords
        parts = re.split(r"[^a-z]+", remaining)
        for part in parts:
            if not part: continue
            
            if part in ("safe", "safety"):
                flags.add(StrategyFlag.SAFE)
            elif part in ("maintain", "keep"):
                flags.add(StrategyFlag.MAINTAIN)
            elif part in ("random", "decay"):
                flags.add(StrategyFlag.RANDOM)
            elif part in ("x", "auto"):
                pass 
            else:
                raise OWOUsageError(f"Unknown strategy flag '{part}' in '{val}'.")
                
        return multiplier, flags
