# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/tools/photo_importer.py
"""
A utility tool to automate the generation of a CSV file with direct links
for all photos stored in a specific Cloudinary folder.
"""

import csv
import logging
import os
from typing import Any, Dict, List, cast

import cloudinary
import cloudinary.api
import cloudinary.uploader

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class CloudinaryPhotoImporter:
    """
    Encapsulates all logic for fetching image data from a Cloudinary folder.

    This class handles authentication, fetching resource lists, transforming
    the data, and writing it to a CSV file.

    Attributes:
        folder_name (str): The name of the Cloudinary folder to process.
        output_csv_file (str): The path to the output CSV file.
    """

    def __init__(self, folder_name: str, output_csv_file: str):
        """
        Initializes the CloudinaryPhotoImporter.

        Args:
            folder_name (str): The name of the folder in Cloudinary to process.
            output_csv_file (str): The path where the CSV file will be saved.
        """
        self.folder_name = folder_name
        self.output_csv_file = output_csv_file

    def _setup_cloudinary(self) -> bool:
        """
        Initializes the Cloudinary SDK with credentials from environment variables.

        Returns:
            bool: True if configuration is successful, False otherwise.
        """
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
        api_key = os.environ.get("CLOUDINARY_API_KEY")
        api_secret = os.environ.get("CLOUDINARY_API_SECRET")

        if not all([cloud_name, api_key, api_secret]):
            logging.error(
                "Cloudinary credentials are not fully configured in your .env file."
            )
            return False

        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
        logging.info(f"Successfully connected to Cloudinary cloud: '{cloud_name}'")
        return True

    def _fetch_image_resources(self) -> List[Dict[str, Any]]:
        """
        Fetches the list of image resources from the specified Cloudinary folder.

        Returns:
            List[Dict[str, Any]]: A list of resource dictionaries from the API,
            or an empty list on failure.
        """
        logging.info(
            f"Searching for images in Cloudinary folder: '{self.folder_name}'..."
        )
        try:
            response = cloudinary.api.resources_by_asset_folder(
                self.folder_name,
                tags=False,
                context=False,
                metadata=False,
                max_results=500,
            )
            resources = response.get("resources", [])
            if not isinstance(resources, list):
                logging.warning("API response for resources is not a list.")
                return []

            logging.info(f"Found {len(resources)} images.")
            return cast(List[Dict[str, Any]], resources)
        except Exception as e:
            logging.error(f"An error occurred while fetching from Cloudinary: {e}")
            return []

    def _transform_to_photo_data(
        self, resources: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Transforms the raw API resource data into the desired CSV format.

        Args:
            resources (List[Dict[str, Any]]): The list of resources from Cloudinary API.

        Returns:
            List[Dict[str, str]]: A list of dictionaries ready to be written to CSV.
        """
        photo_data: List[Dict[str, str]] = []
        for item in resources:
            file_name = item.get("public_id")
            secure_url = item.get("secure_url")
            if not file_name or not secure_url:
                continue

            base_name = os.path.splitext(os.path.basename(file_name))[0].replace(
                "_", " "
            )
            photo_data.append(
                {
                    "photo_name": os.path.basename(file_name),
                    "photo_url": secure_url,
                    "caption": base_name.capitalize(),
                    "family_quotes": "",
                    "used": "FALSE",
                    "date_used": "",
                }
            )
        return photo_data

    def _write_to_csv(self, photo_data: List[Dict[str, str]]) -> None:
        """
        Writes the processed photo data to the output CSV file.

        Args:
            photo_data (List[Dict[str, str]]): The data to be written.
        """
        logging.info(f"Writing {len(photo_data)} records to {self.output_csv_file}...")
        try:
            with open(
                self.output_csv_file, "w", newline="", encoding="utf-8"
            ) as csvfile:
                fieldnames = [
                    "photo_name",
                    "photo_url",
                    "caption",
                    "family_quotes",
                    "used",
                    "date_used",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(photo_data)
            logging.info(f"Successfully created CSV file: {self.output_csv_file}")
            logging.info(
                "You can now import this file into your 'FamilyPhotos' Google Sheet."
            )
        except IOError as e:
            logging.error(f"Could not write to file {self.output_csv_file}: {e}")

    def execute(self) -> None:
        """
        Orchestrates the entire import process from fetching to saving.
        """
        if not self._setup_cloudinary():
            return

        resources = self._fetch_image_resources()
        if not resources:
            return

        photo_data = self._transform_to_photo_data(resources)
        if photo_data:
            self._write_to_csv(photo_data)
        else:
            logging.info("No data to write to CSV.")


def run_importer(folder_name: str, output_csv_file: str) -> None:
    """
    Public-facing function that acts as the entry point for this tool.

    Args:
        folder_name (str): The name of the folder in Cloudinary to process.
        output_csv_file (str): The path to the output CSV file.
    """
    importer = CloudinaryPhotoImporter(folder_name, output_csv_file)
    importer.execute()


# End of src/tools/photo_importer.py (v. 0008)
