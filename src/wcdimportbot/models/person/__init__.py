from typing import Any, Optional

# from wcdimportbot.models.wikimedia.wikipedia.templates.enums import WikipediaTemplatePersonRole
from urllib.parse import urlparse

from wcdimportbot.wcd_base_model import WcdBaseModel


class Person(WcdBaseModel):
    """Model a person mentioned in a page_reference
    Sometimes they are stated as "editor=John Niel"
    and we save that as name_string for later disambiguation"""

    given: Optional[str]
    link: Optional[str]
    mask: Optional[str]
    name_string: Optional[str]
    number_in_sequence: Optional[int]
    orcid: Optional[str]
    # Pydantic 1.9.0 cannot handle hiearchical enums it seems so we use Any here
    role: Any  # should be WikipediaTemplatePersonRole
    surname: Optional[str]

    @property
    def full_name(self) -> str:
        """We hardcode western cultural name ordering pattern here with the
        order "givenname surname".  We use str.strip() because no name has
        significant whitespace at the beginning or end of the string

        We want this property to return either the full name or empty string"""
        if self.name_string:
            # Sometimes the reference has a name string with the "full name"
            # so we try that first
            return self.name_string.strip()
        elif self.given or self.surname:
            # First fallback to given name + surname
            return f"{self.given} {self.surname}".strip()
        else:
            # Second fallback
            return ""

    @property
    def has_number(self) -> bool:
        """This should return True if not None and False otherwise"""
        return bool(self.number_in_sequence)

    @property
    def url(self) -> str:
        url = urlparse(self.link)
        if url.scheme:
            return str(url.geturl())
        else:
            return ""
