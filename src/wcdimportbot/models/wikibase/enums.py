from enum import Enum, auto

# WCD = WikiCitations Database


class KnownArchiveUrl(Enum):
    """Each value in this enum should have a corresponding attribute in the Wikibase class"""

    ARCHIVE_IS = "archive.is"
    ARCHIVE_ORG = "archive.org"
    ARCHIVE_PH = "archive.is"
    ARCHIVE_TODAY = "archive.today"
    GHOSTARCHIVE_ORG = "ghostarchive.org"
    MEMENTOWEB_ORG = "mementoweb.org"
    WEBCITATION_ORG = "webcitation.org"


class SupportedItemType(Enum):
    """The names of this enum must match the attributes in the Wikibase class"""

    WIKIPEDIA_PAGE = auto()
    WIKIPEDIA_REFERENCE = auto()
    WEBSITE_ITEM = auto()
