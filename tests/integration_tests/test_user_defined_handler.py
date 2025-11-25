from unittest.mock import MagicMock, patch
import pytest
from src.handlers.template.user_defined_handler import UserDefinedHandler

MOCK_USER = {
    "description": "Test User",
    "custom_content": {
        "blocks": ["Nezabudni piť vodu", "Cvičiť"],
        "links": [{"title": "Menu", "url": "http://menu.sk"}]
    }
}

@pytest.fixture
def handler():
    # UserReminder má use_cache: false v configu
    config = {"theme_name": "user_reminder", "use_cache": False, "dynamic_image": {"provider": "unsplash"}}
    return UserDefinedHandler(config, "slovak")

@patch("src.handlers.template.user_defined_handler.firestore_service")
@patch("src.handlers.template.user_defined_handler.image_service")
def test_user_reminder_flow(mock_img_service, mock_firestore, handler):
    """Testuje, či sa text skladá z user dát, ale obrázok sa berie z cache."""
    
    # 1. Nastavíme Cache MISS pre obrázok -> musí zavolať Unsplash
    mock_firestore.get_cached_content.return_value = None
    mock_img_service.get_dynamic_image.return_value = {
        "image_url": "http://unsplash.com/photo",
        "attribution_html": "Photo by..."
    }

    # 2. Spustíme
    text, img = handler._process(user=MOCK_USER)

    # 3. Overenia
    assert "Nezabudni piť vodu" in text
    assert '<a href="http://menu.sk">Menu</a>' in text
    assert img == "http://unsplash.com/photo"

    # 4. Kľúčové: Obrázok sa musel uložiť do cache pre ostatných
    mock_firestore.save_cached_content.assert_called()
    args, _ = mock_firestore.save_cached_content.call_args
    assert "user_reminder_SHARED_IMAGE" in args[0]  # Kontrola cache kľúča