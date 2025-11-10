# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/simple_static_models.py
"""
Data models for themes processed by the SimpleStaticHandler.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FamilyPhotoData:
    """
    Represents a single row of data for the 'family_photo' theme.

    The attribute names are prefixed to match the placeholders in the template.

    Attributes:
        photo_url (str): The direct URL to the image file.
        caption (str): The primary caption for the photo.
        family_quote (str): An associated quote about family.
        image_url (str): An alternative attribute for the image URL.
    """

    photo_url: str = ""
    caption: str = ""
    family_quote: str = ""
    image_url: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "FamilyPhotoData":
        """
        Creates a FamilyPhotoData instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            FamilyPhotoData: An initialized instance of the class.
        """
        return cls(
            photo_url=data.get("photo_url", ""),
            caption=data.get("caption", ""),
            family_quote=data.get("family_quotes", ""),
            image_url=data.get("photo_url", ""),
        )


@dataclass
class EuropeanArtData:
    """
    Represents a single row of data for the 'european_art' theme.

    The attribute names are prefixed ('art_') to match the placeholders in the template.

    Attributes:
        art_title (str): The title of the artwork.
        art_artist (str): The name of the artist.
        art_year (str): The year the artwork was completed.
        art_medium (str): The medium used for the artwork.
        art_dimensions (str): The dimensions of the artwork.
        art_owner (str): The current owner or museum.
        art_credit_line (str): The credit line for the artwork.
        art_object_url (str): The URL to the artwork's page.
        image_url (str): The direct URL to the image of the artwork.
    """

    art_title: str = ""
    art_artist: str = ""
    art_year: str = ""
    art_medium: str = ""
    art_dimensions: str = ""
    art_owner: str = ""
    art_credit_line: str = ""
    art_object_url: str = ""
    image_url: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "EuropeanArtData":
        """
        Creates an EuropeanArtData instance from a dictionary, mapping
        sheet columns to prefixed attributes.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            EuropeanArtData: An initialized instance of the class.
        """
        return cls(
            art_title=data.get("title", "N/A"),
            art_artist=data.get("artist", "Unknown"),
            art_year=data.get("year", "N/A"),
            art_medium=data.get("medium", "N/A"),
            art_dimensions=data.get("dimensions", "N/A"),
            art_owner=data.get("owner", "N/A"),
            art_credit_line=data.get("creditLine", "N/A"),
            art_object_url=data.get("objectURL", ""),
            image_url=data.get("image_url", ""),
        )


# End of src/handlers/template/simple_static_models.py (v. 0003)
