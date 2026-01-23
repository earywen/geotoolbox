import pytest
from unittest.mock import patch, MagicMock
from modules import orthohisto, core

class TestOrthohisto:
    
    @pytest.fixture
    def mock_session(self):
        with patch('modules.core.get_session') as mock:
            session = MagicMock()
            mock.return_value = session
            yield session

    def test_ensure_folder_creation(self, tmp_path):
        """Test that ensure_folder creates directory"""
        target = tmp_path / "TimeTravel"
        result = orthohisto.ensure_folder(str(target))
        assert target.exists()
        assert result == str(target)
        
    def test_download_wms_success(self, mock_session, tmp_path):
        """Test successful WMS download configuration"""
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.content = b'fake_image_content_large_enough' * 1000
        mock_session.get.return_value = mock_response
        
        target_file = tmp_path / "test_tile.png"
        
        # Configure Config return
        with patch.dict(core.CONFIG, {'orthohisto': {'wms_url': 'http://test.ign.fr'}}):
            status = orthohisto.download_wms("LAYER_X", str(target_file), "0,0,1,1")
            
        assert status == "OK"
        assert target_file.exists()
        assert target_file.read_bytes() == mock_response.content

    def test_download_wms_empty_image(self, mock_session, tmp_path):
        """Test handling of empty/white images"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.content = b'small' # < 10000 bytes
        mock_session.get.return_value = mock_response
        
        target_file = tmp_path / "empty.png"
        
        with patch.dict(core.CONFIG, {'orthohisto': {'wms_url': 'http://test.ign.fr'}}):
            status = orthohisto.download_wms("LAYER_X", str(target_file), "0,0,1,1")
            
        assert status == "Vide"
        assert not target_file.exists() # Should not save empty file
