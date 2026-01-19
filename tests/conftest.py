import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def fixtures_dir(request):
    """Provides path to golden master fixtures directory."""
    # current file is in tests/
    # fixtures are in tests/test_autolabo/golden_master/
    root_dir = Path(request.config.rootdir)
    return root_dir / "tests" / "test_autolabo" / "golden_master"
