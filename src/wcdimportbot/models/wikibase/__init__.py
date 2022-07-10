from wcdimportbot.wcd_base_model import WcdBaseModel


class Wikibase(WcdBaseModel):
    """This is a parent class for the wikibases we support
    We define all the properties here to be able to use them in the subclasses"""

    botpassword: str
    query_service_url: str
    title: str
    user_name: str
    wikibase_cloud_wikibase: bool = True
    wikibase_url: str

    ACCESS_DATE: str  # date
    ARCHIVE: str  # item
    ARCHIVE_DATE: str  # date
    ARCHIVE_URL: str  # url
    AUTHOR: str  # item
    CHAPTER_URL: str
    CITATIONS: str  # item
    CONFERENCE_URL: str
    DOI: str  # external-id
    EDITOR: str  # item
    EDITOR_NAME_STRING: str  # string
    FAMILY_NAME: str  # string
    FIRST_LEVEL_DOMAIN_STRING: str  # string
    FULL_NAME_STRING: str  # string
    FULL_WORK_AVAILABLE_AT_URL: str  # url
    GIVEN_NAME: str  # string
    GOOGLE_BOOKS_ID: str  # external-id
    HASH: str  # string
    HOST_STRING: str  # string
    INSTANCE_OF: str  # item
    INTERNET_ARCHIVE_ID: str  # external-id
    INTERVIEWER_STRING: str  # string
    ISBN_10: str  # external-id
    ISBN_13: str  # external-id
    ISSUE: str  # string
    LAST_UPDATE: str  # date
    LAY_URL: str
    LOCATION_STRING: str  # string
    LUMPED_AUTHORS: str  # string
    MEDIAWIKI_PAGE_ID: str  # string
    NAME_MASK: str  # string
    OCLC_CONTROL_NUMBER: str  # external-id
    ORCID: str  # external-id
    PAGES: str  # string
    PAGE_REVISION_ID: str  # string
    PERIODICAL_STRING: str  # string
    PMID: str  # external-id
    PUBLICATION_DATE: str  # date
    PUBLISHED_IN: str  # ?
    PUBLISHER_STRING: str  # string
    RETRIEVED_DATE: str  # date
    SERIES_ORDINAL: str  # aka author position # quantity
    SOURCE_WIKIPEDIA: str  # item
    STRING_CITATIONS: str  # string
    TEMPLATE_NAME: str  # string
    TITLE: str  # monolingual text
    TRANSCRIPT_URL: str
    TRANSLATOR_NAME_STRING: str  # string
    URL: str  # url
    VOLUME: str  # string
    WEBSITE: str  # item
    WEBSITE_STRING: str  # string
    WIKIDATA_QID: str  # external id

    ENGLISH_WIKIPEDIA: str = (
        ""  # label: English Wikipedia description: language version of Wikipedia
    )
    WEBSITE_ITEM: str = (
        ""  # label: Website description: first level domain website found in Wikipedia
    )
    WIKIPEDIA_PAGE: str = (
        ""  # label: Wikipedia page description: page in a language version of Wikipedia
    )
    WIKIPEDIA_REFERENCE: str = (
        ""  # label: Wikipedia reference description: reference on a page in Wikipedia
    )
    ARCHIVE_ITEM: str = ""  # label: Archive description: web archive
    ARCHIVE_IS: str = ""  # label: Archive.is description: web archive
    ARCHIVE_ORG: str = ""  # label: Archive.org description: web archive
    ARCHIVE_TODAY: str = ""  # label: Archive.today description: web archive
    WEBCITATION_ORG: str = ""  # label: Webcitation.org description: web archive
    GHOSTARCHIVE_ORG: str = ""

    # This must come last to avoid errors
    wcdqid_language_edition_of_wikipedia_to_work_on: str = ""

    @property
    def mediawiki_api_url(self) -> str:
        return self.wikibase_url + "/w/api.php"

    @property
    def mediawiki_index_url(self) -> str:
        return self.wikibase_url + "/w/index.php"

    @property
    def rdf_entity_prefix(self) -> str:
        return self.rdf_prefix + "/entity/"

    @property
    def rdf_prefix(self) -> str:
        return self.wikibase_url.replace("https", "http")

    @property
    def sparql_endpoint_url(self) -> str:
        if self.wikibase_cloud_wikibase:
            """This is the default endpoint url for Wikibase.cloud instances"""
            return self.wikibase_url + "/query/sparql"
        else:
            """This is the default docker Wikibase endpoint url
            Thanks to @Myst for finding/documenting it."""
            return self.query_service_url + "/proxy/wdqs/bigdata/namespace/wdq/sparql"
