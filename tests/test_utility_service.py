import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from selfbot_discord.services.utility import UtilityService

class TestUtilityService(unittest.TestCase):
    def setUp(self):
        self.service = UtilityService()

    def test_leet_speak(self):
        text = "Hello World"
        expected = "H3ll0 W0rld" # based on map: e->3, l->l(no change in map?), o->0. 
        # Wait, map was: 'a': '4', 'b': '8', 'e': '3', 'g': '9', 'i': '1', 'o': '0', 's': '5', 't': '7', 'z': '2'
        # l is not in map.
        # H -> H
        # e -> 3
        # l -> l
        # l -> l
        # o -> 0
        # W -> W
        # o -> 0
        # r -> r
        # l -> l
        # d -> d
        # So "H3ll0 W0rld"
        self.assertEqual(self.service.leet_speak("Hello World"), "H3ll0 W0rld")

    def test_reverse_text(self):
        self.assertEqual(self.service.reverse_text("abc"), "cba")

    def test_generate_token(self):
        token = self.service.generate_token()
        parts = token.split('.')
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[0]), 24)
        
    def test_minesweeper(self):
        grid = self.service.generate_minesweeper(5, 5, 5)
        self.assertTrue("||" in grid)
        self.assertTrue("\n" in grid)

    @patch('selfbot_discord.services.utility.requests.get')
    def test_get_geoip(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"country": "TestCountry"}
        mock_get.return_value = mock_response
        
        data = self.service.get_geoip("1.1.1.1")
        self.assertEqual(data["country"], "TestCountry")

if __name__ == '__main__':
    unittest.main()
