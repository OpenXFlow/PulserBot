# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/tools/met_artwork_importer.py
"""
A robust utility tool to fetch artwork data from The MET API using an OOP approach.

This module defines the METArtworkImporter class, which handles fetching,
processing, and saving artwork data incrementally to a CSV file. It utilizes
the more efficient /search endpoint and a local cache for the master list of
object IDs to improve performance.
"""

import csv
import logging
import os
import random
import time
from typing import Any, Dict, List, Set, cast

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class METArtworkImporter:
    """
    Encapsulates all logic for fetching and processing artwork from The MET API.

    Attributes:
        department_id (int): The ID of the MET department to query.
        output_file (str): The path to the output CSV file for artwork data.
        id_cache_file (str): The path to the file for caching object IDs.
        max_items (int): The maximum number of new artworks to fetch in a single run.
        existing_ids (Set[int]): A set of object IDs already present in the output file.
    """

    def __init__(
        self,
        department_id: int,
        output_file: str,
        id_cache_file: str,
        max_items: int = 50,
    ):
        """
        Initializes the METArtworkImporter.

        Args:
            department_id (int): The ID of the MET department.
            output_file (str): The path where the CSV file with artwork data will be saved.
            id_cache_file (str): The path where the list of object IDs will be cached.
            max_items (int): The maximum number of new artworks to add in this run.
        """
        self.department_id = department_id
        self.output_file = output_file
        self.id_cache_file = id_cache_file
        self.max_items = max_items
        self.existing_ids: Set[int] = set()

    def _load_existing_ids(self) -> None:
        """Loads already processed object IDs from the existing CSV data file."""
        if not os.path.exists(self.output_file):
            return

        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "object_id" in row and row["object_id"].isdigit():
                        self.existing_ids.add(int(row["object_id"]))
            logging.info(
                f"Loaded {len(self.existing_ids)} existing artwork IDs from '{self.output_file}'."
            )
        except Exception as e:
            logging.warning(f"Could not read existing file '{self.output_file}': {e}")

    def _get_all_artwork_ids_from_api(self) -> List[int]:
        """
        Fetches a filtered list of object IDs using the efficient /search endpoint.

        Returns:
            List[int]: A filtered list of object IDs, or an empty list on failure.
        """
        logging.info("Fetching filtered ID list from MET API /search endpoint...")
        search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"

        # --- FIX: Ensure all param values are strings to satisfy httpx typing ---
        params: Dict[str, str] = {
            "departmentId": str(self.department_id),
            "isPublicDomain": "true",
            "hasImages": "true",
            "q": "*",
        }

        try:
            with httpx.Client(timeout=300.0, headers=HTTP_HEADERS) as client:
                response = client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                object_ids = data.get("objectIDs", [])

                with open(self.id_cache_file, "w", encoding="utf-8") as f:
                    for oid in object_ids:
                        f.write(f"{oid}\n")
                logging.info(
                    f"Saved {len(object_ids)} filtered IDs to cache file '{self.id_cache_file}'."
                )
                return object_ids if object_ids else []
        except Exception as e:
            logging.error(f"Failed to fetch filtered ID list: {e}")
        return []

    def _get_all_artwork_ids(self) -> List[int]:
        """
        Provides the master list of object IDs, prioritizing the local cache.

        Returns:
            List[int]: A list of object IDs.
        """
        if os.path.exists(self.id_cache_file):
            logging.info(f"Loading IDs from cache file: '{self.id_cache_file}'.")
            try:
                with open(self.id_cache_file, "r", encoding="utf-8") as f:
                    return [int(line.strip()) for line in f if line.strip().isdigit()]
            except Exception as e:
                logging.warning(f"Could not read cache file: {e}. Fetching from API.")

        return self._get_all_artwork_ids_from_api()

    def _get_artwork_details(self, object_id: int) -> Dict[str, Any] | None:
        """
        Fetches detailed information for a single artwork object from the MET API.

        Args:
            object_id (int): The ID of the artwork to fetch.

        Returns:
            Dict[str, Any] | None: A dictionary with the artwork's details, or None on failure.
        """
        url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
        try:
            with httpx.Client(timeout=20.0, headers=HTTP_HEADERS) as client:
                response = client.get(url)
                response.raise_for_status()
                return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [403, 429, 502, 503, 504]:
                logging.warning(
                    f"API returned {e.response.status_code} for object {object_id}. Pausing..."
                )
                time.sleep(10)
            else:
                logging.debug(f"HTTP error for object {object_id}: {e}")
        except Exception:
            logging.debug(f"Failed to process object {object_id}.")
        return None

    def _write_data_to_csv(self, artworks_to_add: List[Dict[str, Any]]) -> None:
        """
        Appends a list of new artwork data to the CSV file.

        Args:
            artworks_to_add (List[Dict[str, Any]]): A list of dictionaries representing new artworks.
        """
        file_exists = os.path.exists(self.output_file)
        logging.info(
            f"Appending {len(artworks_to_add)} new artworks to {self.output_file}..."
        )
        try:
            with open(self.output_file, "a", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "object_id",
                    "title",
                    "artist",
                    "year",
                    "image_url",
                    "owner",
                    "medium",
                    "dimensions",
                    "classification",
                    "creditLine",
                    "objectURL",
                    "artistULAN_URL",
                    "tags",
                    "used",
                    "date_used",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(artworks_to_add)
            logging.info("Successfully appended new artworks.")
        except IOError as e:
            logging.error(f"Could not write to file: {e}")

    def execute(self) -> None:
        """Orchestrates the entire import process from fetching to saving."""
        self._load_existing_ids()
        all_object_ids = self._get_all_artwork_ids()
        if not all_object_ids:
            return

        ids_to_process_pool = list(set(all_object_ids) - self.existing_ids)
        if not ids_to_process_pool:
            logging.info(
                "All available artworks from this search are already in the CSV file."
            )
            return

        logging.info(f"Pool of new IDs to process: {len(ids_to_process_pool)}")
        random.shuffle(ids_to_process_pool)

        artworks_to_add: List[Dict[str, Any]] = []

        for i, object_id in enumerate(ids_to_process_pool):
            if len(artworks_to_add) >= self.max_items:
                logging.info(
                    f"Reached the batch limit of {self.max_items} new items. Stopping."
                )
                break

            logging.info(f"Processing candidate {i + 1} (ID: {object_id})...")
            details = self._get_artwork_details(object_id)

            if details:
                tags_list = details.get("tags", [])
                tags_str = (
                    "; ".join(tag.get("term", "") for tag in tags_list if tag)
                    if tags_list
                    else ""
                )
                artworks_to_add.append(
                    {
                        "object_id": details.get("objectID"),
                        "title": details.get("title", "N/A"),
                        "artist": details.get("artistDisplayName", "Unknown"),
                        "year": details.get("objectEndDate", "N/A"),
                        "image_url": details.get("primaryImageSmall"),
                        "owner": "The Metropolitan Museum of Art, New York",
                        "medium": details.get("medium", "N/A"),
                        "dimensions": details.get("dimensions", "N/A"),
                        "classification": details.get("classification", "N/A"),
                        "creditLine": details.get("creditLine", "N/A"),
                        "objectURL": details.get("objectURL", ""),
                        "artistULAN_URL": details.get("artistULAN_URL", ""),
                        "tags": tags_str,
                        "used": "FALSE",
                        "date_used": "",
                    }
                )
                logging.info(f" -> Added '{details.get('title')}'")

            time.sleep(random.uniform(0.3, 0.8))
            if (i + 1) % 50 == 0:
                logging.info("--- Taking a 5-second break ---")
                time.sleep(5)

        if artworks_to_add:
            self._write_data_to_csv(artworks_to_add)
        else:
            logging.warning("No new valid artworks were found in this run.")


def run_importer(
    department_id: int, output_file: str, id_cache_file: str, max_items: int = 50
) -> None:
    """
    Public-facing function that acts as the entry point for this tool.

    Args:
        department_id (int): The ID of the MET department to query.
        output_file (str): The path to the output CSV file for artwork data.
        id_cache_file (str): The path to the file for caching object IDs.
        max_items (int): The maximum number of new artworks to fetch.
    """
    importer = METArtworkImporter(department_id, output_file, id_cache_file, max_items)
    importer.execute()


# End of src/tools/met_artwork_importer.py (v. 0017)
