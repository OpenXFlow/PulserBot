from unittest.mock import MagicMock, patch
import pytest
from src.handlers._base.base_handler import BaseHandler

# Vytvoríme "Dummy" handler na testovanie Base triedy
class DummyHandler(BaseHandler):
    def _process(self, user=None, **kwargs):
        return "New Content", "http://new.image"

@pytest.fixture
def handler():
    config = {"theme_name": "test_theme", "use_cache": True}
    return DummyHandler(config, "sk")

@patch("src.handlers._base.base_handler.firestore_service")
def test_execute_cache_hit(mock_firestore, handler):
    """Ak je obsah v cache, _process() sa NESMIE spustiť."""
    # 1. Nastavíme, že cache vráti dáta
    mock_firestore.get_cached_content.return_value = {
        "text": "Cached Text",
        "image_url": "http://cached.image"
    }

    # 2. Spustíme execute
    text, img = handler.execute()

    # 3. Overenie
    assert text == "Cached Text"
    assert img == "http://cached.image"
    # _process by sa nemal volať (tu to nemáme ako overiť priamo na inštancii, 
    # ale vieme, že návratová hodnota je z cache)
    
    # Dôležité: Save sa nesmie volať pri HITe
    mock_firestore.save_cached_content.assert_not_called()

@patch("src.handlers._base.base_handler.firestore_service")
def test_execute_cache_miss(mock_firestore, handler):
    """Ak cache chýba, musí sa spustiť _process() a uložiť výsledok."""
    # 1. Cache vráti None
    mock_firestore.get_cached_content.return_value = None

    # 2. Spustíme execute
    text, img = handler.execute()

    # 3. Overenie
    assert text == "New Content"
    
    # Musí sa zavolať uloženie do cache
    mock_firestore.save_cached_content.assert_called_once()