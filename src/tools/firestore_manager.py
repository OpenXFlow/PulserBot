# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/tools/firestore_manager.py
"""
Utility module for backing up and restoring Firestore user data.
"""

import json
import logging
import os
from datetime import datetime

from src.services import firestore_service


class FirestoreManager:
    """
    Manages backup and restore operations for Firestore data.
    """

    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize the manager.

        Args:
            backup_dir (str): Directory where backups will be stored.
        """
        self.backup_dir = backup_dir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logging.info(f"Created backup directory: {self.backup_dir}")

    def backup_users(self) -> str:
        """
        Fetches all users from Firestore and saves them to a JSON file.

        Returns:
            str: Path to the created backup file.
        """
        logging.info("Starting Firestore user backup...")

        # We can reuse the service, but we might need a method to get ALL users,
        # not just active ones. For backup, we want everything.
        # Let's access the internal client directly for raw access.
        db = firestore_service._firestore_service_instance._db
        if not db:
            logging.error("Firestore client not initialized.")
            return ""

        try:
            users_ref = db.collection("users")
            docs = users_ref.stream()

            all_users = {}
            count = 0
            for doc in docs:
                user_data = doc.to_dict()
                # Convert Firestore timestamp to string for JSON serialization
                if "lastUpdated" in user_data:
                    try:
                        user_data["lastUpdated"] = user_data["lastUpdated"].isoformat()
                    except AttributeError:
                        pass  # It's already a string or other type

                all_users[doc.id] = user_data
                count += 1

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firestore_users_backup_{timestamp}.json"
            filepath = os.path.join(self.backup_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_users, f, indent=2, ensure_ascii=False)

            logging.info(f"Backup successful! Saved {count} users to: {filepath}")
            return filepath

        except Exception as e:
            logging.exception(f"Backup failed: {e}")
            return ""

    def restore_users(self, backup_file: str) -> None:
        """
        Restores users from a JSON backup file to Firestore.
        WARNING: This overwrites existing data for matching IDs.

        Args:
            backup_file (str): Path to the JSON backup file.
        """
        logging.warning(f"Starting RESTORE process from: {backup_file}")
        logging.warning("This will overwrite existing user data in Firestore.")

        confirmation = input("Are you sure you want to proceed? (yes/no): ")
        if confirmation.lower() != "yes":
            logging.info("Restore cancelled.")
            return

        db = firestore_service._firestore_service_instance._db
        if not db:
            logging.error("Firestore client not initialized.")
            return

        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                users_data = json.load(f)

            batch = db.batch()
            count = 0

            for uid, data in users_data.items():
                doc_ref = db.collection("users").document(uid)

                # Clean up timestamp strings back to server timestamp on write
                # or keep them as strings/dates if preferred.
                # For simplicity, we update 'lastUpdated' to now.
                if "lastUpdated" in data:
                    del data[
                        "lastUpdated"
                    ]  # Let Firestore handle update time if needed or ignore

                batch.set(doc_ref, data, merge=True)
                count += 1

                # Firestore batches have a limit (500 ops), commit periodically
                if count % 400 == 0:
                    batch.commit()
                    batch = db.batch()
                    logging.info(f"Committed batch of {count} records...")

            batch.commit()
            logging.info(f"Restore complete. Processed {count} users.")

        except Exception as e:
            logging.exception(f"Restore failed: {e}")


def run_backup() -> None:
    manager = FirestoreManager()
    manager.backup_users()


def run_restore(file_path: str) -> None:
    manager = FirestoreManager()
    manager.restore_users(file_path)


# End of src/tools/firestore_manager.py (v. 0001)
