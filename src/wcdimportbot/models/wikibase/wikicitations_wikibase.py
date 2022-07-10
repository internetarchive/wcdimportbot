import config
from wcdimportbot.models.wikibase import Wikibase


class WikiCitationsWikibase(Wikibase):
    """This models the properties and items on wikicitations.wiki.opencura.com"""

    title = "wikicitations.wiki.opencura.com"
    user_name = config.user
    botpassword = config.pwd
    wikibase_url = "https://wikicitations.wiki.opencura.com"
    query_service_url = wikibase_url + "/query/"

    OCLC_CONTROL_NUMBER = ""
    GOOGLE_BOOKS_ID = ""
    INTERNET_ARCHIVE_ID = ""
    PERIODICAL_STRING = ""
    ACCESS_DATE = "P37"
    ARCHIVE = "P52"
    ARCHIVE_DATE = "P39"
    ARCHIVE_URL = "P38"
    AUTHOR = "P7"
    FULL_NAME_STRING = "P15"
    DOI = "P33"
    EDITOR = "P6"
    EDITOR_NAME_STRING = "P40"
    FAMILY_NAME = "P5"
    GIVEN_NAME = "P4"
    CITATIONS = "P19"
    FIRST_LEVEL_DOMAIN_STRING = "P49"
    FULL_WORK_AVAILABLE_AT_URL = "P23"
    HASH = "P30"
    HOST_STRING = "P47"
    INSTANCE_OF = "P10"
    INTERVIEWER_STRING = "P48"
    ISBN_10 = "P28"
    ISBN_13 = "P32"
    ISSUE = "P24"
    LAST_UPDATE = "P43"
    LOCATION_STRING = "P51"
    LUMPED_AUTHORS = "P46"
    MEDIAWIKI_PAGE_ID = "P18"
    NAME_MASK = "P45"
    ORCID = "P31"
    PAGES = "P25"
    PMID = "P34"
    PUBLICATION_DATE = "P12"
    PUBLISHED_IN = "P17"
    PUBLISHER_STRING = "P50"
    RETRIEVED_DATE = "P29"
    PAGE_REVISION_ID = "P42"  # string
    SERIES_ORDINAL = "P14"  # aka author position # quantity
    SOURCE_WIKIPEDIA = "P9"
    STRING_CITATIONS = "P36"
    TEMPLATE_NAME = "P8"
    TITLE = "P20"  # monolingual text
    TRANSLATOR_NAME_STRING = "P41"
    URL = "P2"
    VOLUME = "P27"
    WEBSITE = "P13"
    WEBSITE_STRING = "P35"
    WIKIDATA_QID = "P44"  # external id

    CHAPTER_URL = ""
    CONFERENCE_URL = ""
    LAY_URL = ""
    TRANSCRIPT_URL = ""

    ARCHIVE_IS = "Q5830"
    ARCHIVE_ORG = "Q5660"
    ARCHIVE_PH = "Q5830"
    ARCHIVE_TODAY = ""
    ENGLISH_WIKIPEDIA = "Q3"
    MEMENTOWEB_ORG = ""
    WEBCITATION_ORG = ""
    WEBSITE_ITEM = "Q145"
    WIKIPEDIA_PAGE = "Q6"
    WIKIPEDIA_REFERENCE = "Q4"

    # This has to come last to work.
    wcdqid_language_edition_of_wikipedia_to_work_on = ENGLISH_WIKIPEDIA
