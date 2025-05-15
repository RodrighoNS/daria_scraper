"""
Character model representing a character from the Daria series.
"""

class Character:
    """Model representing a character from the Daria series."""

    def __init__(self, url=""):
        """
        Initialize a character model.

        Args:
            url: URL of the character's page
        """
        self.url = url
        self.full_name = ""
        self.alter_egos_images = []

    def to_dict(self):
        """
        Convert the character model to a dictionary.

        Returns:
            Dictionary representation of the character
        """
        return {
            "url": self.url,
            "full_name": self.full_name,
            "alter_egos_images": self.alter_egos_images
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a character model from a dictionary.

        Args:
            data: Dictionary with character data

        Returns:
            Character instance
        """
        character = cls(data.get("url", ""))
        character.full_name = data.get("full_name", "")
        character.alter_egos_images = data.get("alter_egos_images", [])
        return character
