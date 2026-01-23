import io
import random
import string
import requests
import pyfiglet
from gtts import gTTS
import qrcode
from PIL import Image

class UtilityService:
    """Service for handling utility tasks like GeoIP, TTS, QR, etc."""

    def get_geoip(self, ip: str) -> dict | None:
        """Fetch GeoIP information for a given I P address."""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def generate_tts(self, text: str) -> io.BytesIO:
        """Generate TTS audio from text."""
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp

    def generate_qr(self, text: str) -> io.BytesIO:
        """Generate a QR code image from text."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        fp = io.BytesIO()
        img.save(fp, format='PNG')
        fp.seek(0)
        return fp

    def generate_token(self) -> str:
        """Generate a fake Discord token."""
        # Standard token format: ID.Selector.HMAC
        # ID is base64 encoded snowflake
        # We'll just generate random parts for the look
        part1 = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
        part2 = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        part3 = ''.join(random.choices(string.ascii_letters + string.digits + "-_", k=27))
        return f"{part1}.{part2}.{part3}"

    def generate_nitro(self) -> str:
        """Generate a fake Nitro gift link."""
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return f"https://discord.gift/{code}"

    def leet_speak(self, text: str) -> str:
        """Convert text to leet speak."""
        replacements = {
            'a': '4', 'b': '8', 'e': '3', 'g': '9', 'i': '1', 
            'o': '0', 's': '5', 't': '7', 'z': '2'
        }
        return ''.join(replacements.get(c.lower(), c) for c in text)

    def ascii_art(self, text: str) -> str:
        """Convert text to ASCII art."""
        try:
            return pyfiglet.figlet_format(text)
        except Exception:
            return text

    def reverse_text(self, text: str) -> str:
        """Reverse the given text."""
        return text[::-1]

    def generate_minesweeper(self, width: int, height: int, bombs: int) -> str:
        """Generate a minesweeper grid with spoiler tags."""
        if width > 13: width = 13
        if height > 13: height = 13
        if bombs > width * height: bombs = width * height - 1

        grid = [[0 for _ in range(width)] for _ in range(height)]
        
        # Place bombs
        bomb_locs = set()
        while len(bomb_locs) < bombs:
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            if (x, y) not in bomb_locs:
                grid[y][x] = -1
                bomb_locs.add((x, y))

        # Calculate numbers
        for y in range(height):
            for x in range(width):
                if grid[y][x] == -1:
                    continue
                count = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0: continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == -1:
                            count += 1
                grid[y][x] = count

        # Convert to discord format
        output = ""
        emojis = {
            -1: "💥", 0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 
            4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"
        }
        
        for row in grid:
            for cell in row:
                char = emojis.get(cell, "❓")
                output += f"||{char}||"
            output += "\n"
            
        return output

    def get_dick_size(self, user_id: int) -> int:
        """Deterministically calculate 'size' based on user ID."""
        # Use user ID as seed to always get same result for same user
        random.seed(user_id)
        size = random.randint(0, 30)
        random.seed() # Reset seed
        return size
