import sys
import os
import logging
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.cartographie_core.vector_fetcher import fetch_features
from modules import core

# Setup simple logging
logging.basicConfig(level=logging.INFO)

class TestVectorLayers(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Ensure config loaded
        if hasattr(core, 'init'):
            core.init()
        elif hasattr(core, 'load_config'):
            core.load_config()

    def test_znieff1_retrieval(self):
        # Area known to have ZNIEFF1 (Rouen)
        bbox = {
            'min_lon': 1.0, 'min_lat': 49.4,
            'max_lon': 1.1, 'max_lat': 49.5
        }
        features = fetch_features("ZNIEFF1", bbox, mode='preview')
        print(f"ZNIEFF1 Features found: {len(features)}")
        self.assertGreater(len(features), 0, "Should find ZNIEFF1 features in Rouen area")

    def test_ppri_retrieval(self):
        bbox = {
            'min_lon': 1.0, 'min_lat': 49.4,
            'max_lon': 1.1, 'max_lat': 49.5
        }
        features = fetch_features("PPRI", bbox, mode='preview')
        print(f"PPRI Features found: {len(features)}")
        self.assertGreater(len(features), 0, "Should find PPRI features in Rouen area")

if __name__ == "__main__":
    unittest.main()
