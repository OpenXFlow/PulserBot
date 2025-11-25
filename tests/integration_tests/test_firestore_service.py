from unittest.mock import MagicMock, patch
import pytest
from src.services.firestore_service import FirestoreService

@patch("src.services.firestore_service.firebase_admin")
@patch("src.services.firestore_service.firestore")
def test_get_active_users_from_snapshot(mock_firestore, mock_admin):
    """Simuluje načítanie používateľov z cache (snapshotu)."""
    
    service = FirestoreService()
    # Mock DB klienta
    mock_db = MagicMock()
    service._db = mock_db

    # 1. Simulujeme, že metadata dokument existuje
    mock_metadata_doc = MagicMock()
    mock_metadata_doc.exists = True
    mock_metadata_doc.to_dict.return_value = {"chunks_count": 1, "total_users": 2}
    
    # 2. Simulujeme chunk dokument
    mock_chunk_doc = MagicMock()
    mock_chunk_doc.exists = True
    mock_chunk_doc.to_dict.return_value = {
        "users": [
            {"email": "user1@test.com", "active": True},
            {"email": "user2@test.com", "active": True}
        ]
    }

    # Nastavenie side_effect pre postupné volania .document().get()
    # Prvé volanie je metadata, druhé je chunk_0
    mock_db.collection.return_value.document.return_value.get.side_effect = [
        mock_metadata_doc, 
        mock_chunk_doc
    ]

    # 3. Volanie
    users = service.get_active_users(force_refresh=False)

    # 4. Overenie
    assert len(users) == 2
    assert users[0]["email"] == "user1@test.com"
    # Overíme, že sa NEVOLALO 'where' (čiže nešlo sa do ostrej DB)
    mock_db.collection.return_value.where.assert_not_called()