import pytest
import os
import json
import hashlib
from freezegun import freeze_time
from datetime import datetime
from pathlib import Path
import logging
from modules.autolabo import process_and_export

# --- Helper Functions ---
def calculate_file_hash(path):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# --- Fixtures ---
@pytest.fixture(scope="session")
def hashes_file(fixtures_dir):
    return fixtures_dir / "golden_master_hashes.json"

@pytest.fixture(scope="session")
def golden_hashes(hashes_file):
    with open(hashes_file, "r") as f:
        return json.load(f)

# --- Tests ---
@pytest.mark.golden
class TestGoldenMaster:
    """Golden Master Tests for AutoLabo."""

    def test_agrolab_eaux_golden_master(self, fixtures_dir, golden_hashes, tmp_path):
        """Verify Agrolab Eaux output matches Golden Master hash."""
        self._verify_hash("agrolab_eaux", fixtures_dir, golden_hashes, tmp_path)

    def test_eurofins_eaux_golden_master(self, fixtures_dir, golden_hashes, tmp_path):
        """Verify Eurofins Eaux output matches Golden Master hash."""
        self._verify_hash("eurofins_eaux", fixtures_dir, golden_hashes, tmp_path)

    def test_agrolab_sols_golden_master(self, fixtures_dir, golden_hashes, tmp_path):
        """Verify Agrolab Sols output matches Golden Master hash."""
        self._verify_hash("agrolab_sols", fixtures_dir, golden_hashes, tmp_path)

    def _verify_hash(self, key, fixtures_dir, golden_hashes, tmp_path):
        """Generic verification logic."""
        expected_hash = golden_hashes.get(key)
        assert expected_hash, f"Hash for {key} not found in hashes file."

        # Input Path
        input_filename = f"{key}_sample.xlsx"
        input_path = str(fixtures_dir / "fixtures" / input_filename)
        assert os.path.exists(input_path), f"Input file {input_path} missing."

        # Provider & Model
        parts = key.split("_")
        provider = parts[0]
        model = "es" if "eaux" in parts[1] else "sols"

        # Output Target
        target_dir = str(tmp_path)
        
        # Run Process with FreezeGun Mocked Datetime
        # Must match the time used in generate_fixtures.py
        with freeze_time("2023-01-01 12:00:00"):
            result = process_and_export([input_path], model_id=model, target_path=target_dir, provider_id=provider)

        assert result["success"], f"Processing failed: {result.get('error')}"
        output_path = result["output_path"]
        assert os.path.exists(output_path), "Output file not found."

        # Calculate Hash
        actual_hash = calculate_file_hash(output_path)
        
        # Comparison
        assert actual_hash == expected_hash, (
            f"Hash mismatch for {key}.\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}\n"
            "This suggests a regression in output generation or binary structure."
        )
