from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from selfbot_discord.services.owo.models import BettingSide, MultiplierMode


class OWOUsageError(Exception):
    """Exception raised for invalid CLI arguments."""


@dataclass
class StartParams:
    amount: int
    multiplier_mode: MultiplierMode = MultiplierMode.STATIC
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

        # Legacy check: if arg[0] is not a flag, handle legacy shortcuts
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
            # Unknown non-flag argument -> assume invalid or usage
            return CLIResult(action="usage")
        action = "start" # Default
        
        base_bet: int | None = None
        multiplier_mode = MultiplierMode.STATIC
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
                
                if val == "auto":
                    multiplier_mode = MultiplierMode.AUTO
                else:
                    # Regex to match: x?([number])(-)?([mode])?
                    # Examples: x2, x2.5, x2-safe, safe, maintain, x3-maintain
                    match = re.match(r"^x?(\d*\.?\d+)(?:-?([a-zA-Z]+))?$|^([a-zA-Z]+)$", val)
                    
                    if match:
                        # Group 1: Number (if present)
                        # Group 2: Mode (if present after number)
                        # Group 3: Mode (if ONLY mode)
                        
                        num_str = match.group(1)
                        mode_suffix = match.group(2)
                        only_mode = match.group(3)
                        
                        # Determine Mode
                        mode_str = (mode_suffix or only_mode or "").lower()
                        
                        if mode_str in ("safe", "safety"):
                            multiplier_mode = MultiplierMode.SAFE
                        elif mode_str in ("maintain", "keep"):
                            multiplier_mode = MultiplierMode.MAINTAIN
                        elif mode_str in ("random", "decay"):
                            multiplier_mode = MultiplierMode.RANDOM_DECAY
                        elif not mode_str:
                            multiplier_mode = MultiplierMode.STATIC
                        else:
                            raise OWOUsageError(f"Unknown mode '{mode_str}' in '{val}'.")
                            
                        # Determine Multiplier
                        if num_str:
                            try:
                                static_multiplier = float(num_str)
                            except ValueError:
                                raise OWOUsageError(f"Invalid multiplier number: {num_str}")
                        else:
                            # Default multiplier if only mode is specified (e.g. "-e safe")
                            static_multiplier = 2.0
                            
                    else:
                        raise OWOUsageError(f"Invalid format '{val}'. Examples: x2, x3-safe, maintain")

            elif arg in ("-side", "--side", "-sd"):
                if i + 1 >= len(args):
                    raise OWOUsageError("Missing value for `-side` flag.")
                val = args[i+1].lower()
                i += 1

                if val in ("h", "head", "heads"):
                    betting_side = BettingSide.HEADS
                elif val in ("t", "tail", "tails"):
                    betting_side = BettingSide.TAILS
                elif val in ("r", "rand", "random"):
                     betting_side = BettingSide.RANDOM
                else:
                     raise OWOUsageError(f"Invalid side: {val}. Use h, t, or r.")
            
            i += 1

        if base_bet is None:
            if action == "start":
                return CLIResult(action="usage")
        
        return CLIResult(
            action="start",
            start_params=StartParams(
                amount=base_bet,
                multiplier_mode=multiplier_mode,
                static_multiplier=static_multiplier,
                betting_side=betting_side
            )
        )
