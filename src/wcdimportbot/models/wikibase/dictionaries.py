"""
This file holds all the data about our needed properties and semantic "base" items.

One item is missing here and hardcoded into
setup_all_properties_and_items_on_new_wikibase.py for now
"""
from wikibaseintegrator.wbi_enums import WikibaseDatatype  # type: ignore

wcd_archive_items = dict(
    ARCHIVE_IS=dict(label="Archive.is", description="web archive"),
    ARCHIVE_ORG=dict(label="Archive.org", description="web archive"),
    ARCHIVE_TODAY=dict(label="Archive.today", description="web archive"),
    GHOSTARCHIVE_ORG=dict(label="Ghostarchive.org", description="web archive"),
    WEBCITATION_ORG=dict(label="Webcitation.org", description="web archive"),
)

wcd_items = dict(
    ENGLISH_WIKIPEDIA=dict(
        label="English Wikipedia", description="language version of Wikipedia"
    ),
    WEBSITE_ITEM=dict(
        label="Website", description="first level domain website found in Wikipedia"
    ),
    WIKIPEDIA_PAGE=dict(
        label="Wikipedia page", description="page in a language version of Wikipedia"
    ),
    WIKIPEDIA_REFERENCE=dict(
        label="Wikipedia reference", description="reference on a page in Wikipedia"
    ),
)


wcd_externalid_properties = dict(
    DOI=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
    GOOGLE_BOOKS_ID=dict(
        datatype=WikibaseDatatype.EXTERNALID,
        description="Identifier used to link books at Google.",
    ),
    INTERNET_ARCHIVE_ID=dict(
        datatype=WikibaseDatatype.EXTERNALID,
        description="Identifier used to link books and "
        "other resources at Internet Archive.",
    ),
    ISBN_10=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
    ISBN_13=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
    MEDIAWIKI_PAGE_ID=dict(
        # this is string in WCD
        datatype=WikibaseDatatype.EXTERNALID,
        description="",
    ),
    OCLC_CONTROL_NUMBER=dict(
        datatype=WikibaseDatatype.EXTERNALID,
        description="Online Computer Library Centers control number in Worldcat",
    ),
    ORCID=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
    PMID=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
    WIKIDATA_QID=dict(datatype=WikibaseDatatype.EXTERNALID, description=""),
)

wcd_item_properties = dict(
    ARCHIVE=dict(datatype=WikibaseDatatype.ITEM, description=""),
    AUTHOR=dict(datatype=WikibaseDatatype.ITEM, description=""),
    CITATIONS=dict(datatype=WikibaseDatatype.ITEM, description=""),
    EDITOR=dict(datatype=WikibaseDatatype.ITEM, description=""),
    INSTANCE_OF=dict(datatype=WikibaseDatatype.ITEM, description=""),
    PUBLISHED_IN=dict(datatype=WikibaseDatatype.ITEM, description=""),
    SOURCE_WIKIPEDIA=dict(datatype=WikibaseDatatype.ITEM, description=""),
    WEBSITE=dict(datatype=WikibaseDatatype.ITEM, description=""),
)

wcd_quantity_properties = dict(
    SERIES_ORDINAL=dict(datatype=WikibaseDatatype.QUANTITY, description=""),
)

wcd_string_properties = dict(
    EDITOR_NAME_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    FAMILY_NAME=dict(datatype=WikibaseDatatype.STRING, description=""),
    FIRST_LEVEL_DOMAIN_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    FULL_NAME_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    GIVEN_NAME=dict(datatype=WikibaseDatatype.STRING, description=""),
    HASH=dict(datatype=WikibaseDatatype.STRING, description=""),
    HOST_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    INTERVIEWER_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    ISSUE=dict(datatype=WikibaseDatatype.STRING, description=""),
    LOCATION_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    LUMPED_AUTHORS=dict(datatype=WikibaseDatatype.STRING, description=""),
    NAME_MASK=dict(datatype=WikibaseDatatype.STRING, description=""),
    PAGES=dict(datatype=WikibaseDatatype.STRING, description=""),
    PAGE_REVISION_ID=dict(datatype=WikibaseDatatype.STRING, description=""),
    PERIODICAL_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    PUBLISHER_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    STRING_CITATIONS=dict(datatype=WikibaseDatatype.STRING, description=""),
    TEMPLATE_NAME=dict(datatype=WikibaseDatatype.STRING, description=""),
    TITLE=dict(datatype=WikibaseDatatype.STRING, description=""),
    TRANSLATOR_NAME_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
    VOLUME=dict(datatype=WikibaseDatatype.STRING, description=""),
    WEBSITE_STRING=dict(datatype=WikibaseDatatype.STRING, description=""),
)

wcd_url_properties = dict(
    ARCHIVE_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    CHAPTER_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    CONFERENCE_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    FULL_WORK_AVAILABLE_AT_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    LAY_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    TRANSCRIPT_URL=dict(datatype=WikibaseDatatype.URL, description=""),
    URL=dict(datatype=WikibaseDatatype.URL, description=""),
)
wcd_time_properties = dict(
    ACCESS_DATE=dict(
        datatype=WikibaseDatatype.TIME, description="date of access of the resource"
    ),
    ARCHIVE_DATE=dict(datatype=WikibaseDatatype.TIME, description=""),
    LAST_UPDATE=dict(
        datatype=WikibaseDatatype.TIME, description="date of last update of this item?"
    ),
    PUBLICATION_DATE=dict(
        datatype=WikibaseDatatype.TIME,
        description="date of publication of the resource",
    ),
    RETRIEVED_DATE=dict(
        datatype=WikibaseDatatype.TIME, description="date of retrieval of the resource"
    ),
)
