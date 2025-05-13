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
        self.current_age = ""
        self.current_vocation = ""
        self.season_one_age = ""
        self.season_one_vocation = ""
        self.parents = ""
        self.siblings = ""
        self.first_appearance = ""
        self.status_at_end_of_series = ""
        self.character_on_self = ""
        self.description = []
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
            "current_age": self.current_age,
            "current_vocation": self.current_vocation,
            "season_one_age": self.season_one_age,
            "season_one_vocation": self.season_one_vocation,
            "parents": self.parents,
            "siblings": self.siblings,
            "first_appearance": self.first_appearance,
            "status_at_end_of_series": self.status_at_end_of_series,
            "character_on_self": self.character_on_self,
            "description": self.description,
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
        character.current_age = data.get("current_age", "")
        character.current_vocation = data.get("current_vocation", "")
        character.season_one_age = data.get("season_one_age", "")
        character.season_one_vocation = data.get("season_one_vocation", "")
        character.parents = data.get("parents", "")
        character.siblings = data.get("siblings", "")
        character.first_appearance = data.get("first_appearance", "")
        character.status_at_end_of_series = data.get("status_at_end_of_series", "")
        character.character_on_self = data.get("character_on_self", "")
        character.description = data.get("description", [])
        character.alter_egos_images = data.get("alter_egos_images", [])
        return character
