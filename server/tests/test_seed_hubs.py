import unittest

from data.seed_hubs import SEED_HUBS


class SeedHubTests(unittest.TestCase):
    def test_every_seed_hub_has_coordinates(self):
        new_york = next(hub for hub in SEED_HUBS if hub["city"] == "New York")
        denver = next(hub for hub in SEED_HUBS if hub["city"] == "Denver")
        self.assertEqual(len(SEED_HUBS), 14)
        self.assertTrue(all("latitude" in hub["location"] and "longitude" in hub["location"] for hub in SEED_HUBS))
        self.assertEqual(new_york["location"]["county"], "New York")
        self.assertEqual(denver["location"]["state_code"], "CO")
