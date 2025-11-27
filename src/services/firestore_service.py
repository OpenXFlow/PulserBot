# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/firestore_service.py
"""
Service module for interacting with Google Cloud Firestore.

This module handles the initialization of the Firebase Admin SDK and provides
methods to fetch user data directly from the database, utilizing a daily
snapshot caching strategy to minimize read operations.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import firebase_admin
from firebase_admin import credentials, firestore

from ..config import ZoneInfo

# Constants
USER_SNAPSHOT_CHUNK_SIZE = 2000


class FirestoreService:
    """
    Encapsulates all interactions with the Firestore database.
    """

    def __init__(self) -> None:
        """Initializes the FirestoreService."""
        self._db = None
        self._initialize_app()

    def _initialize_app(self) -> None:
        """Initializes the Firebase Admin app singleton."""
        try:
            if not firebase_admin._apps:
                cred_path = os.environ.get(
                    "GOOGLE_APPLICATION_CREDENTIALS", "credentials.json"
                )

                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logging.info(f"Firebase Admin initialized using: {cred_path}")
                else:
                    logging.info(
                        "Credentials file not found. Attempting default initialization."
                    )
                    firebase_admin.initialize_app()

            self._db = firestore.client()

        except Exception as e:
            logging.critical(f"Failed to initialize Firebase Admin: {e}", exc_info=True)
            self._db = None

    def get_active_users(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetches active users, utilizing a Chunked Daily Snapshot Cache.

        Args:
            force_refresh (bool): If True, ignores existing snapshot and fetches live data.

        Returns:
            List[Dict[str, Any]]: List of user configurations.
        """
        if not self._db:
            logging.error("Firestore DB client is not ready. Cannot fetch users.")
            return []

        today_str = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%d")
        metadata_doc_id = f"users_{today_str}"

        try:
            cache_collection = self._db.collection("system_cache")
            metadata_ref = cache_collection.document(metadata_doc_id)

            # --- 1. CACHE HIT PATH (Only if NOT forced) ---
            if not force_refresh:
                metadata_doc = metadata_ref.get()
                if metadata_doc.exists:
                    meta_data = metadata_doc.to_dict()
                    chunks_count = meta_data.get("chunks_count", 0)
                    total_users = meta_data.get("total_users", 0)

                    logging.info(
                        f"User Snapshot HIT: Metadata found ({total_users} users)."
                    )

                    all_users = []
                    for i in range(chunks_count):
                        chunk_id = f"{metadata_doc_id}_chunk_{i}"
                        chunk_doc = cache_collection.document(chunk_id).get()
                        if chunk_doc.exists:
                            chunk_data = chunk_doc.to_dict()
                            all_users.extend(chunk_data.get("users", []))

                    return all_users
            else:
                logging.info("User Snapshot: Force refresh requested. Ignoring cache.")

            # --- 2. CACHE MISS / FORCE REFRESH PATH (Live Fetch) ---
            logging.info(f"Fetching live user data for snapshot '{metadata_doc_id}'...")

            users_ref = self._db.collection("users")
            query = users_ref.where(filter=firestore.FieldFilter("active", "==", True))
            docs = query.stream()

            users_list = []
            for doc in docs:
                user_data = doc.to_dict()
                user_data["firestore_uid"] = doc.id
                if "lastUpdated" in user_data:
                    del user_data["lastUpdated"]
                users_list.append(user_data)

            # --- 3. SAVE TO CACHE ---
            total_count = len(users_list)
            if total_count > 0:
                try:
                    batch = self._db.batch()
                    chunks = [
                        users_list[i : i + USER_SNAPSHOT_CHUNK_SIZE]
                        for i in range(0, total_count, USER_SNAPSHOT_CHUNK_SIZE)
                    ]

                    for i, chunk in enumerate(chunks):
                        chunk_doc_ref = cache_collection.document(
                            f"{metadata_doc_id}_chunk_{i}"
                        )
                        batch.set(chunk_doc_ref, {"users": chunk})

                    batch.set(
                        metadata_ref,
                        {
                            "created_at": firestore.SERVER_TIMESTAMP,
                            "total_users": total_count,
                            "chunks_count": len(chunks),
                        },
                    )

                    batch.commit()
                    logging.info(f"User Snapshot UPDATED: Saved {total_count} users.")
                except Exception as e:
                    logging.error(f"Failed to save User Snapshot: {e}")

            return users_list

        except Exception as e:
            logging.exception(f"Error in get_active_users: {e}")
            return []

    def get_cached_content(self, theme_id: str, date_str: str) -> Dict[str, Any] | None:
        if not self._db:
            return None
        doc_id = f"{date_str}_{theme_id}"
        try:
            doc_ref = self._db.collection("daily_content_cache").document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                logging.info(f"Content Cache HIT for {doc_id}")
                return doc.to_dict().get("content")
            else:
                logging.info(f"Content Cache MISS for {doc_id}")
                return None
        except Exception as e:
            logging.error(f"Error reading content cache: {e}")
            return None

    def save_cached_content(
        self, theme_id: str, date_str: str, data: Dict[str, Any]
    ) -> None:
        if not self._db:
            return
        doc_id = f"{date_str}_{theme_id}"
        try:
            doc_ref = self._db.collection("daily_content_cache").document(doc_id)
            cache_doc = {
                "created_at": firestore.SERVER_TIMESTAMP,
                "theme_id": theme_id,
                "date": date_str,
                "content": data,
            }
            doc_ref.set(cache_doc)
            logging.info(f"Content cached successfully: {doc_id}")
        except Exception as e:
            logging.error(f"Error saving content cache: {e}")


# Singleton Instance
_firestore_service_instance = FirestoreService()


def get_active_users(force_refresh: bool = False) -> List[Dict[str, Any]]:
    return _firestore_service_instance.get_active_users(force_refresh)


def get_cached_content(theme_id: str, date_str: str) -> Dict[str, Any] | None:
    return _firestore_service_instance.get_cached_content(theme_id, date_str)


def save_cached_content(theme_id: str, date_str: str, data: Dict[str, Any]) -> None:
    _firestore_service_instance.save_cached_content(theme_id, date_str, data)


# End of src/services/firestore_service.py (v. 0005)
