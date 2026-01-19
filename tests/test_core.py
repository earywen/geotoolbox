import pytest
from unittest.mock import patch, MagicMock
import os
from modules import core
from modules.core import load_template, SecurityError
import requests

# Fixture to mock CONFIG
@pytest.fixture
def mock_config():
    original_config = core.CONFIG.copy()
    core.CONFIG.update({
        'network': {
            'verify_ssl': True,
            'user_agent': 'TestAgent/1.0'
        },
        'discord': {
            'webhook_url': 'https://discord.com/api/webhooks/test'
        }
    })
    yield
    core.CONFIG = original_config

class TestCoreSession:
    def test_get_session_ssl_verified(self, mock_config):
        """Test that get_session respects verify_ssl=True"""
        core.CONFIG['network']['verify_ssl'] = True
        session = core.get_session()
        assert session.verify is True
        assert session.headers['User-Agent'] == 'TestAgent/1.0'

    def test_get_session_ssl_disabled(self, mock_config):
        """Test that get_session respects verify_ssl=False and logs warning"""
        core.CONFIG['network']['verify_ssl'] = False
        with patch('modules.core.logging.warning') as mock_log:
            session = core.get_session()
            assert session.verify is False
            mock_log.assert_called_with("⚠️  SSL VERIFICATION DISABLED - This should only be used in development!")

class TestLoadTemplate:
    @pytest.fixture
    def mock_fs(self, tmp_path):
        """Setup a fake assets/templates directory"""
        assets = tmp_path / "assets" / "templates"
        assets.mkdir(parents=True)
        (assets / "valid.html").write_text("Valid Content", encoding='utf-8')
        return assets

    def test_load_template_valid_file(self, mock_fs):
        """Test loading a valid template file"""
        with patch('modules.core.get_base_path', return_value=str(mock_fs.parent.parent)):
            content = load_template("valid.html")
            assert content == "Valid Content"

    def test_load_template_not_found(self, mock_fs):
        """Test loading a non-existent file"""
        with patch('modules.core.get_base_path', return_value=str(mock_fs.parent.parent)):
            with patch('modules.core.logging.error') as mock_log:
                content = load_template("missing.html")
                assert "Erreur: Impossible de charger missing.html" in content
                # Note: The implementation returns an HTML error string, doesn't raise

    def test_load_template_path_traversal(self, mock_fs):
        """Test path traversal protection"""
        with patch('modules.core.get_base_path', return_value=str(mock_fs.parent.parent)):
            with pytest.raises(SecurityError, match="Path traversal attempt detected"):
                load_template("../../../secret.txt")

    def test_load_template_absolute_path_attack(self, mock_fs):
        """Test absolute path traversal attempt"""
        # On Windows, absolute paths usually have a drive letter, e.g. C:/Windows/calc.exe
        # We try to access something clearly outside the templates folder
        target = "C:/Windows/win.ini" if os.name == 'nt' else "/etc/passwd"
        
        with patch('modules.core.get_base_path', return_value=str(mock_fs.parent.parent)):
             # The implementation uses .resolve() and .relative_to()
             # If target is outside base, relative_to raises ValueError -> caught as SecurityError
            with pytest.raises(SecurityError):
                load_template(target)
