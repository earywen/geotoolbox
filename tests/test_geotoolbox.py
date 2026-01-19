import pytest
from unittest.mock import patch, MagicMock
from modules import core, geotoolbox
from modules.core import MockAdapter, UI_ADAPTER, WebviewAdapter

# Fixture to swap adapter
@pytest.fixture
def mock_ui():
    mock = MockAdapter()
    original_adapter = core.UI_ADAPTER
    core.UI_ADAPTER = mock
    yield mock
    core.UI_ADAPTER = original_adapter

# Fixture to mock Fetcher
@pytest.fixture
def mock_fetcher():
    with patch('modules.geotoolbox.fetch_features') as mock:
        yield mock

class TestGeotoolboxPreview:
    def test_preview_logic_basic(self, mock_ui, mock_fetcher):
        """Test basic preview flow with mocked data"""
        
        # Setup specific mock return
        mock_fetcher.return_value = [
            {'id': 'BSS001', 'code_bss': 'BSS/123', 'LATITUDE_APPROX': 45.0, 'geometry': {}, 'niveau_eau_scrappe': 'Unknown'}
        ]
        
        bbox = {"xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1}
        # Use a real layer key from models or a mocked one if possible
        # We rely on LAYERS_CONFIG. let's assume 'ADES_MONITORED_PTS' exists or similar
        # Or better, we patch LAYERS_CONFIG to ensure we have a valid test key
        
        with patch.dict(geotoolbox.LAYERS_CONFIG, {
            'TEST_LAYER': {'label': 'Test Layer', 'name_field': 'code_bss', 'color': 'red'}
        }):
            results = geotoolbox.run_preview_logic(bbox, ['TEST_LAYER'])

        # Verify Results
        assert len(results) == 1
        assert results[0]['layer'] == 'Test Layer'
        assert results[0]['count'] == 1
        assert results[0]['items'][0]['nom'] == 'BSS/123'

        # Verify Events via MockAdapter
        # Should have loader_update events
        assert len(mock_ui.events) > 0
        events_names = [e[0] for e in mock_ui.events]
        assert 'loader_update' in events_names
        assert 'loader_hide' in events_names

    def test_preview_logic_empty(self, mock_ui, mock_fetcher):
        """Test preview with no results"""
        mock_fetcher.return_value = []
        
        with patch.dict(geotoolbox.LAYERS_CONFIG, {
            'TEST_LAYER_EMPTY': {'label': 'Test Empty', 'name_field': 'id', 'color': 'blue'}
        }):
            results = geotoolbox.run_preview_logic({}, ['TEST_LAYER_EMPTY'])
            
        assert len(results) == 1
        assert results[0]['count'] == 0
