import re
from dataclasses import dataclass
from enum import Enum, auto

class OWOUsageError(Exception):
    pass

class MultiplierMode(Enum):
    STATIC = auto()
    AUTO = auto()
    SAFE = auto()
    MAINTAIN = auto()
    RANDOM_DECAY = auto()

# Mock parser logic reproduction because we can't easily import OWOArgParser directly if it has complex dependencies
# But verification should use the REAL code if possible. 
# Let's try to import the real class first. If that fails (deps), we use the regex logic directly to test the REGEX.

def test_parse(val):
    print(f"\nScanning: '{val}'")
    try:
        match = re.match(r"^x?(\d*\.?\d+)(?:-?([a-zA-Z]+))?$|^([a-zA-Z]+)$", val)
        if match:
            num_str = match.group(1)
            mode_suffix = match.group(2)
            only_mode = match.group(3)
            
            print(f"  Match Groups: Num='{num_str}', Suffix='{mode_suffix}', OnlyMode='{only_mode}'")
            
            mode_str = (mode_suffix or only_mode or "").lower()
            
            # Simulate Logic
            # Determine Mode
            if mode_str in ("safe", "safety"):
                mode = MultiplierMode.SAFE
            elif mode_str in ("maintain", "keep"):
                mode = MultiplierMode.MAINTAIN
            elif mode_str in ("random", "decay"):
                mode = MultiplierMode.RANDOM_DECAY
            elif not mode_str:
                mode = MultiplierMode.STATIC
            else:
                 print(f"  ❌ Unknown Mode: {mode_str}")
                 return

            # Determine Multiplier
            if num_str:
                mult = float(num_str)
            else:
                mult = 2.0
            
            print(f"  ✅ Result: Mode={mode.name}, Mult={mult}")
        else:
            print("  ❌ No Regex Match")

    except Exception as e:
        print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    test_cases = [
        "x2", "x3", "x1.5",
        "safe", "maintain", "random",
        "x2-safe", "x3-maintain", "x1.5-random",
        "2-safe", "3.0-maintain",
        "x100-safe",
        "invalid", "x2-invalid"
    ]
    
    for t in test_cases:
        test_parse(t)
