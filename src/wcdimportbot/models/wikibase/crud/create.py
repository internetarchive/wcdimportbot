import logging
import textwrap
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import validate_arguments
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_login  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import (  # type: ignore
    Claim,
    Qualifiers,
    Reference,
    References,
)
from wikibaseintegrator.wbi_exceptions import ModificationFailed  # type: ignore

import config
from wcdimportbot.helpers import console
from wcdimportbot.models.exceptions import MissingInformationError
from wcdimportbot.models.person import Person
from wcdimportbot.models.wikibase.crud import WikibaseCrud
from wcdimportbot.models.wikimedia.wikipedia.templates.wikipedia_page_reference import (
    WikipediaPageReference,
)

if TYPE_CHECKING:
    from wcdimportbot.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

logger = logging.getLogger(__name__)


class WikibaseCrudCreate(WikibaseCrud):
    @validate_arguments
    def __prepare_all_person_claims__(
        self, page_reference: WikipediaPageReference
    ) -> List[Claim]:
        if not self.wikibase.FULL_NAME_STRING:
            raise MissingInformationError(
                "self.wikibase.FULL_NAME_STRING was empty string"
            )
        if not self.wikibase.EDITOR_NAME_STRING:
            raise MissingInformationError(
                "self.wikibase.EDITOR_NAME_STRING was empty string"
            )
        if not self.wikibase.HOST_STRING:
            raise MissingInformationError("self.wikibase.HOST_STRING was empty string")
        if not self.wikibase.INTERVIEWER_STRING:
            raise MissingInformationError(
                "self.wikibase.INTERVIEWER_STRING was empty string"
            )
        authors = self.__prepare_person_claims__(
            use_list=page_reference.authors_list,
            property=self.wikibase.FULL_NAME_STRING,
        )
        if (
            config.assume_persons_without_role_are_authors
            and page_reference.persons_without_role
        ):
            logger.info("Assuming persons without role are authors")
        no_role_authors = self.__prepare_person_claims__(
            use_list=page_reference.persons_without_role,
            property=self.wikibase.FULL_NAME_STRING,
        )
        editors = self.__prepare_person_claims__(
            use_list=page_reference.interviewers_list,
            property=self.wikibase.EDITOR_NAME_STRING,
        )
        hosts = self.__prepare_person_claims__(
            use_list=page_reference.hosts_list,
            property=self.wikibase.HOST_STRING,
        )
        interviewers = self.__prepare_person_claims__(
            use_list=page_reference.interviewers_list,
            property=self.wikibase.INTERVIEWER_STRING,
        )
        translators = self.__prepare_person_claims__(
            use_list=page_reference.interviewers_list,
            property=self.wikibase.INTERVIEWER_STRING,
        )
        return authors + no_role_authors + editors + hosts + interviewers + translators

    @validate_arguments
    def __prepare_item_citations__(
        self, wikipedia_page  # type: WikipediaPage
    ) -> List[Claim]:
        """Prepare the item citations and add a reference
        to in which revision it was found and the retrieval date"""
        logger.info("Preparing item citations")
        claims = []
        for reference in wikipedia_page.references or []:
            if reference.wikicitations_qid:
                logger.debug("Appending to citations")
                claims.append(
                    datatypes.Item(
                        prop_nr=self.wikibase.CITATIONS,
                        value=reference.wikicitations_qid,
                        references=self.reference_claim,
                    )
                )
        return claims

    @validate_arguments
    def __prepare_new_reference_item__(
        self,
        page_reference: WikipediaPageReference,
        wikipedia_page,  # type: WikipediaPage
    ) -> ItemEntity:
        """This method converts a page_reference into a new reference item"""
        self.__setup_wikibase_integrator_configuration__()
        logger.debug(f"Trying to log in to the Wikibase as {self.wikibase.user_name}")
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=self.wikibase.user_name, password=self.wikibase.botpassword
            ),
        )
        item = wbi.item.new()
        if page_reference.md5hash:
            # We append the first 7 chars of the hash to the title
            # to avoid label collision errors
            # Wikibase does not allow a label longer than 250 characters maximum
            if page_reference.title:
                shortened_title = textwrap.shorten(
                    page_reference.title, width=240, placeholder="..."
                )
            else:
                # Handle title being None
                shortened_title = "Title missing"
            label = f"{shortened_title} | {page_reference.md5hash[:7]}"
            item.labels.set("en", label)
            item.descriptions.set(
                "en", f"reference from {wikipedia_page.wikimedia_site.name.title()}"
            )
            persons = self.__prepare_all_person_claims__(page_reference=page_reference)
            if persons:
                item.add_claims(persons)
            item.add_claims(
                claims=self.__prepare_single_value_reference_claims__(
                    page_reference=page_reference
                )
            )
            # if config.loglevel == logging.DEBUG:
            #     logger.debug("Printing the item data")
            #     print(item.get_json())
            #     # exit()
            return item
        else:
            raise MissingInformationError("page_reference.md5hash was empty")

    @validate_arguments
    def __prepare_new_website_item__(
        self,
        page_reference: WikipediaPageReference,
        wikipedia_page,  # type: WikipediaPage
    ) -> ItemEntity:
        """This method converts a page_reference into a new website item"""
        if page_reference.first_level_domain_of_url is None:
            raise MissingInformationError(
                "page_reference.first_level_domain_of_url was None"
            )
        logger.info(
            f"Creating website item: {page_reference.first_level_domain_of_url}"
        )
        self.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=self.wikibase.user_name, password=self.wikibase.botpassword
            ),
        )
        item = wbi.item.new()
        item.labels.set("en", page_reference.first_level_domain_of_url)
        item.descriptions.set(
            "en",
            f"website referenced from {wikipedia_page.wikimedia_site.name.title()}",
        )
        item.add_claims(
            self.__prepare_single_value_website_claims__(page_reference=page_reference),
        )
        # if config.loglevel == logging.DEBUG:
        #     logger.debug("Printing the item data")
        #     print(item.get_json())
        #     # exit()
        return item

    @validate_arguments
    def __prepare_new_wikipedia_page_item__(
        self, wikipedia_page  # type: WikipediaPage
    ) -> ItemEntity:
        """This method converts a page_reference into a new WikiCitations item"""
        logging.debug("__prepare_new_wikipedia_page_item__: Running")
        self.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=self.wikibase.user_name, password=self.wikibase.botpassword
            ),
        )
        item = wbi.item.new()
        if wikipedia_page.title:
            shortened_title = textwrap.shorten(
                wikipedia_page.title, width=250, placeholder="..."
            )
        else:
            shortened_title = None
        item.labels.set("en", shortened_title)
        item.descriptions.set(
            "en",
            f"page from {wikipedia_page.language_code}:{wikipedia_page.wikimedia_site.name.title()}",
        )
        # Prepare claims
        # First prepare the page_reference needed in other claims
        citations = self.__prepare_item_citations__(wikipedia_page=wikipedia_page)
        string_citations = self.__prepare_string_citations__(
            wikipedia_page=wikipedia_page
        )
        if citations:
            item.add_claims(citations)
        if string_citations:
            item.add_claims(string_citations)
        item.add_claims(
            self.__prepare_single_value_wikipedia_page_claims__(
                wikipedia_page=wikipedia_page
            ),
        )
        if config.loglevel == logging.DEBUG:
            logger.debug("Printing the item data")
            print(item.get_json())
            # exit()
        return item

    @validate_arguments
    def __prepare_person_claims__(
        self,
        use_list: Optional[List[Person]],
        property: str,
    ) -> List:
        """Prepare claims using the specified property and list of person objects"""
        persons = []
        use_list = use_list or []
        if use_list:
            logger.debug(f"Preparing {property}")
            for person_object in use_list:
                # We use this pythonic way of checking if the string is empty inspired by:
                # https://www.delftstack.com/howto/python/how-to-check-a-string-is-empty-in-a-pythonic-way/
                if person_object.full_name:
                    qualifiers = (
                        self.__prepare_person_qualifiers__(person_object=person_object)
                        or []
                    )
                    if qualifiers:
                        person = datatypes.String(
                            prop_nr=property,
                            value=person_object.full_name,
                            qualifiers=qualifiers,
                        )
                    else:
                        person = datatypes.String(
                            prop_nr=property,
                            value=person_object.full_name,
                        )
                    persons.append(person)
        return persons

    @validate_arguments
    def __prepare_person_qualifiers__(self, person_object: Person):
        qualifiers = []
        if (
            person_object.given
            or person_object.given
            or person_object.orcid
            or person_object.number_in_sequence
        ):
            if person_object.given:
                given_name = datatypes.String(
                    prop_nr=self.wikibase.GIVEN_NAME,
                    value=person_object.given,
                )
                qualifiers.append(given_name)
            if person_object.surname:
                surname = datatypes.String(
                    prop_nr=self.wikibase.FAMILY_NAME,
                    value=person_object.surname,
                )
                qualifiers.append(surname)
            if person_object.number_in_sequence:
                number_in_sequence = datatypes.Quantity(
                    prop_nr=self.wikibase.SERIES_ORDINAL,
                    amount=person_object.number_in_sequence,
                )
                qualifiers.append(number_in_sequence)
            if person_object.orcid:
                orcid = datatypes.ExternalID(
                    prop_nr=self.wikibase.ORCID,
                    value=person_object.orcid,
                )
                qualifiers.append(orcid)
            if person_object.url:
                url = datatypes.URL(
                    prop_nr=self.wikibase.URL,
                    value=person_object.url,
                )
                qualifiers.append(url)
            if person_object.mask:
                mask = datatypes.String(
                    prop_nr=self.wikibase.NAME_MASK,
                    value=person_object.mask,
                )
                qualifiers.append(mask)
        return qualifiers

    @validate_arguments
    def __prepare_reference_claim__(
        self, wikipedia_page  # type: WikipediaPage
    ):
        """This reference claim contains the current revision id and the current date
        This enables us to track references over time in the graph using SPARQL."""
        logger.info("Preparing reference claim")
        # Prepare page_reference
        retrieved_date = datatypes.Time(
            prop_nr=self.wikibase.RETRIEVED_DATE,
            time=datetime.utcnow()  # Fetched today
            .replace(tzinfo=timezone.utc)
            .replace(
                hour=0,
                minute=0,
                second=0,
            )
            .strftime("+%Y-%m-%dT%H:%M:%SZ"),
        )
        revision_id = datatypes.String(
            prop_nr=self.wikibase.PAGE_REVISION_ID,
            value=str(wikipedia_page.latest_revision_id),
        )
        claims = [retrieved_date, revision_id]
        citation_reference = Reference()
        for claim in claims:
            logger.debug(f"Adding reference {claim}")
            citation_reference.add(claim)
        self.reference_claim = References()
        self.reference_claim.add(citation_reference)

    @validate_arguments
    def __prepare_single_value_reference_claims__(
        self,
        page_reference: WikipediaPageReference,
    ) -> List[Claim]:
        logger.info("Preparing single value claims")
        if page_reference.md5hash is None:
            raise ValueError("page_reference.md5hash was None")
        # Website item
        if page_reference.first_level_domain_of_url_qid:
            website_item = datatypes.Item(
                prop_nr=self.wikibase.WEBSITE,
                value=page_reference.first_level_domain_of_url_qid,
            )
        else:
            website_item = None
        claims: List[Claim] = []
        for claim in (website_item,):
            if claim:
                claims.append(claim)
        return (
            claims
            + self.__prepare_single_value_reference_claims_always_present__(
                page_reference=page_reference
            )
            + self.__prepare_single_value_reference_external_identifier_claims__(
                page_reference=page_reference
            )
            + self.__prepare_single_value_reference_string_claims__(
                page_reference=page_reference
            )
            + self.__prepare_single_value_reference_claims_with_dates__(
                page_reference=page_reference
            )
            + self.__prepare_single_value_reference_claims_with_urls__(
                page_reference=page_reference
            )
        )

    @validate_arguments
    def __prepare_single_value_reference_claims_always_present__(
        self,
        page_reference: WikipediaPageReference,
    ) -> List[Claim]:
        instance_of = datatypes.Item(
            prop_nr=self.wikibase.INSTANCE_OF,
            value=self.wikibase.WIKIPEDIA_REFERENCE,
        )
        hash_claim = datatypes.String(
            prop_nr=self.wikibase.HASH, value=page_reference.md5hash
        )
        if page_reference.template_name:
            template_string = datatypes.String(
                prop_nr=self.wikibase.TEMPLATE_NAME,
                value=page_reference.template_name,
            )
        else:
            raise ValueError("no template name found")
        retrieved_date = datatypes.Time(
            prop_nr=self.wikibase.RETRIEVED_DATE,
            time=datetime.utcnow()  # Fetched today
            .replace(tzinfo=timezone.utc)
            .replace(
                hour=0,
                minute=0,
                second=0,
            )
            .strftime("+%Y-%m-%dT%H:%M:%SZ"),
        )
        if not self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on:
            raise MissingInformationError(
                "self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on was None"
            )
        source_wikipedia = datatypes.Item(
            prop_nr=self.wikibase.SOURCE_WIKIPEDIA,
            value=self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on,
        )
        return [
            hash_claim,
            instance_of,
            retrieved_date,
            source_wikipedia,
            template_string,
        ]

    @validate_arguments
    def __prepare_single_value_reference_external_identifier_claims__(
        self,
        page_reference: WikipediaPageReference,
    ) -> List[Claim]:
        if page_reference.google_books_id:
            google_books_id = datatypes.ExternalID(
                prop_nr=self.wikibase.GOOGLE_BOOKS_ID,
                value=page_reference.google_books_id,
            )
        else:
            google_books_id = None
        if page_reference.internet_archive_id:
            internet_archive_id = datatypes.ExternalID(
                prop_nr=self.wikibase.INTERNET_ARCHIVE_ID,
                value=page_reference.internet_archive_id,
            )
        else:
            internet_archive_id = None
        if page_reference.doi:
            doi = datatypes.ExternalID(
                prop_nr=self.wikibase.DOI,
                value=page_reference.doi,
            )
        else:
            doi = None
        if page_reference.isbn_10:
            isbn_10 = datatypes.ExternalID(
                prop_nr=self.wikibase.ISBN_10,
                value=page_reference.isbn_10,
            )
        else:
            isbn_10 = None
        if page_reference.isbn_13:
            isbn_13 = datatypes.ExternalID(
                prop_nr=self.wikibase.ISBN_13,
                value=page_reference.isbn_13,
            )
        else:
            isbn_13 = None
        if page_reference.oclc:
            oclc = datatypes.ExternalID(
                prop_nr=self.wikibase.OCLC_CONTROL_NUMBER,
                value=page_reference.oclc,
            )
        else:
            oclc = None
        if page_reference.orcid:
            orcid = datatypes.ExternalID(
                prop_nr=self.wikibase.ORCID,
                value=page_reference.orcid,
            )
        else:
            orcid = None
        if page_reference.pmid:
            pmid = datatypes.ExternalID(
                prop_nr=self.wikibase.PMID,
                value=page_reference.pmid,
            )
        else:
            pmid = None
        if page_reference.wikidata_qid:
            wikidata_qid = datatypes.ExternalID(
                prop_nr=self.wikibase.WIKIDATA_QID,
                value=page_reference.wikidata_qid,
            )
        else:
            wikidata_qid = None
        claims: List[Claim] = []
        for claim in (
            doi,
            google_books_id,
            internet_archive_id,
            isbn_10,
            isbn_13,
            oclc,
            orcid,
            pmid,
            wikidata_qid,
        ):
            if claim:
                claims.append(claim)
        return claims

    @validate_arguments
    def __prepare_single_value_reference_string_claims__(
        self,
        page_reference: WikipediaPageReference,
    ) -> List[Claim]:
        if page_reference.location:
            location = datatypes.String(
                prop_nr=self.wikibase.LOCATION_STRING, value=page_reference.location
            )
        else:
            location = None
        if page_reference.vauthors:
            lumped_authors = datatypes.String(
                prop_nr=self.wikibase.LUMPED_AUTHORS,
                value=page_reference.vauthors,
            )
        else:
            lumped_authors = None
        if page_reference.periodical:
            periodical_string = datatypes.String(
                prop_nr=self.wikibase.PERIODICAL_STRING,
                value=page_reference.periodical,
            )
        else:
            periodical_string = None
        if page_reference.publisher:
            publisher = datatypes.String(
                prop_nr=self.wikibase.PUBLISHER_STRING,
                value=page_reference.publisher,
            )
        else:
            publisher = None
        if page_reference.title:
            # Wikibase has a default limit of 400 chars for String
            shortened_title = textwrap.shorten(
                page_reference.title, width=400, placeholder="..."
            )
            title = datatypes.String(
                prop_nr=self.wikibase.TITLE,
                value=shortened_title,
            )
        else:
            title = None
        if page_reference.website:
            website_string = datatypes.String(
                prop_nr=self.wikibase.WEBSITE_STRING,
                value=page_reference.website,
            )
        else:
            website_string = None
        claims: List[Claim] = []
        for claim in (
            location,
            lumped_authors,
            periodical_string,
            publisher,
            title,
            website_string,
        ):
            if claim:
                claims.append(claim)
        return claims

    @validate_arguments
    def __prepare_single_value_reference_claims_with_dates__(
        self,
        page_reference: WikipediaPageReference,
    ) -> List[Claim]:
        claims = []
        if page_reference.access_date:
            claims.append(
                datatypes.Time(
                    prop_nr=self.wikibase.ACCESS_DATE,
                    time=(
                        page_reference.access_date.replace(tzinfo=timezone.utc)
                        .replace(
                            hour=0,
                            minute=0,
                            second=0,
                        )
                        .strftime("+%Y-%m-%dT%H:%M:%SZ")
                    ),
                )
            )
        if page_reference.publication_date:
            claims.append(
                datatypes.Time(
                    prop_nr=self.wikibase.PUBLICATION_DATE,
                    time=(
                        page_reference.publication_date.replace(tzinfo=timezone.utc)
                        .replace(
                            hour=0,
                            minute=0,
                            second=0,
                        )
                        .strftime("+%Y-%m-%dT%H:%M:%SZ")
                    ),
                )
            )
        return claims

    def __prepare_single_value_reference_claims_with_urls__(
        self, page_reference
    ) -> List[Claim]:
        claims = []
        if page_reference.archive_url:
            if len(page_reference.archive_url) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                if page_reference.detected_archive_of_archive_url:
                    claims.append(
                        datatypes.URL(
                            prop_nr=self.wikibase.ARCHIVE_URL,
                            value=page_reference.archive_url,
                            qualifiers=[
                                datatypes.Item(
                                    prop_nr=self.wikibase.ARCHIVE,
                                    value=self.wikibase.__getattribute__(
                                        page_reference.detected_archive_of_archive_url.name.upper().replace(
                                            ".", "_"
                                        )
                                    ),
                                )
                            ],
                        )
                    )
                else:
                    message = f"No supported archive detected for {page_reference.archive_url}"
                    self.__log_to_file__(
                        message=message, file_name="undetected_archive.log"
                    )
                    claims.append(
                        datatypes.URL(
                            prop_nr=self.wikibase.ARCHIVE_URL,
                            value=page_reference.archive_url,
                        )
                    )
        if page_reference.url:
            if len(page_reference.url) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                claims.append(
                    datatypes.URL(
                        prop_nr=self.wikibase.URL,
                        value=page_reference.url,
                    )
                )
        if page_reference.chapter_url:
            if len(page_reference.chapter_url) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                claims.append(
                    datatypes.URL(
                        prop_nr=self.wikibase.CHAPTER_URL,
                        value=page_reference.chapter_url,
                    )
                )
        if page_reference.conference_url:
            if len(page_reference.conference_url) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                claims.append(
                    datatypes.URL(
                        prop_nr=self.wikibase.CONFERENCE_URL,
                        value=page_reference.conference_url,
                    )
                )
        if page_reference.lay_url:
            if len(page_reference.lay_url) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                claims.append(
                    datatypes.URL(
                        prop_nr=self.wikibase.LAY_URL,
                        value=page_reference.lay_url,
                    )
                )
        if page_reference.transcripturl:
            if len(page_reference.transcripturl) > 500:
                # TODO log to file also
                logger.error(
                    f"Skipping statement for this URL because it "
                    f"is too long for Wikibase currently to store :/"
                )
            else:
                claims.append(
                    datatypes.URL(
                        prop_nr=self.wikibase.TRANSCRIPT_URL,
                        value=page_reference.transcripturl,
                    )
                )
        return claims

    @validate_arguments
    def __prepare_single_value_website_claims__(
        self,
        page_reference: WikipediaPageReference,
    ) -> Optional[List[Claim]]:
        logger.info("Preparing single value claims for the website item")
        # Claims always present
        instance_of = datatypes.Item(
            prop_nr=self.wikibase.INSTANCE_OF,
            value=self.wikibase.WEBSITE_ITEM,
        )
        if not self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on:
            raise MissingInformationError(
                "self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on was None"
            )
        source_wikipedia = datatypes.Item(
            prop_nr=self.wikibase.SOURCE_WIKIPEDIA,
            value=self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on,
        )
        first_level_domain_string = datatypes.String(
            prop_nr=self.wikibase.FIRST_LEVEL_DOMAIN_STRING,
            value=page_reference.first_level_domain_of_url,
        )
        if page_reference.first_level_domain_of_url_hash is None:
            raise ValueError("page_reference.first_level_domain_of_url_hash was None")
        hash_claim = datatypes.String(
            prop_nr=self.wikibase.HASH,
            value=page_reference.first_level_domain_of_url_hash,
        )
        return [
            claim
            for claim in (
                instance_of,
                source_wikipedia,
                first_level_domain_string,
                hash_claim,
            )
            if claim
        ]

    def __prepare_single_value_wikipedia_page_claims__(
        self, wikipedia_page
    ) -> List[Claim]:
        # There are no optional claims for Wikipedia Pages
        absolute_url = datatypes.URL(
            prop_nr=self.wikibase.URL,
            value=wikipedia_page.absolute_url,
        )
        if wikipedia_page.md5hash is None:
            raise ValueError("wikipedia_page.md5hash was None")
        hash_claim = datatypes.String(
            prop_nr=self.wikibase.HASH, value=wikipedia_page.md5hash
        )
        instance_of = datatypes.Item(
            prop_nr=self.wikibase.INSTANCE_OF,
            value=self.wikibase.WIKIPEDIA_PAGE,
        )
        last_update = datatypes.Time(
            prop_nr=self.wikibase.LAST_UPDATE,
            time=datetime.utcnow()  # Fetched today
            .replace(tzinfo=timezone.utc)
            .replace(
                hour=0,
                minute=0,
                second=0,
            )
            .strftime("+%Y-%m-%dT%H:%M:%SZ"),
        )
        if wikipedia_page.page_id is None:
            raise ValueError("wikipedia_page.page_id was None")
        page_id = datatypes.String(
            prop_nr=self.wikibase.MEDIAWIKI_PAGE_ID,
            value=str(wikipedia_page.page_id),
        )
        if not self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on:
            raise MissingInformationError(
                "self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on was None"
            )
        published_in = datatypes.Item(
            prop_nr=self.wikibase.PUBLISHED_IN,
            value=self.wikibase.wcdqid_language_edition_of_wikipedia_to_work_on,
        )
        if wikipedia_page.title is None:
            raise ValueError("wikipedia_page.item_id was None")
        title = datatypes.String(
            prop_nr=self.wikibase.TITLE,
            value=wikipedia_page.title,
        )
        return [
            absolute_url,
            hash_claim,
            instance_of,
            last_update,
            page_id,
            published_in,
            title,
        ]

    def __prepare_string_authors__(self, page_reference: WikipediaPageReference):
        authors = []
        for author in page_reference.authors_list or []:
            if author.full_name:
                author = datatypes.String(
                    prop_nr=self.wikibase.FULL_NAME_STRING,
                    value=author.full_name,
                )
                authors.append(author)
        if page_reference.vauthors:
            author = datatypes.String(
                prop_nr=self.wikibase.LUMPED_AUTHORS,
                value=page_reference.vauthors,
            )
            authors.append(author)
        if page_reference.authors:
            author = datatypes.String(
                prop_nr=self.wikibase.LUMPED_AUTHORS,
                value=page_reference.authors,
            )
            authors.append(author)
        return authors or None

    def __prepare_string_editors__(self, page_reference: WikipediaPageReference):
        persons = []
        for person in page_reference.editors_list or []:
            if person.full_name:
                person = datatypes.String(
                    prop_nr=self.wikibase.EDITOR_NAME_STRING,
                    value=person.full_name,
                )
                persons.append(person)
        return persons or None

    def __prepare_string_translators__(self, page_reference: WikipediaPageReference):
        persons = []
        for person in page_reference.translators_list or []:
            if person.full_name:
                person = datatypes.String(
                    prop_nr=self.wikibase.TRANSLATOR_NAME_STRING,
                    value=person.full_name,
                )
                persons.append(person)
        return persons or None

    @validate_arguments()
    def __prepare_string_citation__(
        self, page_reference: WikipediaPageReference
    ) -> Claim:
        """We import citations which could not be uniquely identified
        as strings directly on the wikipedia page item"""
        qualifiers = self.__prepare_string_citation_qualifiers__(
            page_reference=page_reference
        )
        claim_qualifiers = Qualifiers()
        for qualifier in qualifiers:
            logger.debug(f"Adding qualifier {qualifier}")
            claim_qualifiers.add(qualifier)
        string_citation = datatypes.String(
            prop_nr=self.wikibase.STRING_CITATIONS,
            value=page_reference.template_name,
            qualifiers=claim_qualifiers,
            references=self.reference_claim,
        )
        return string_citation

    @validate_arguments
    def __prepare_string_citation_qualifiers__(
        self, page_reference: WikipediaPageReference
    ) -> List[Claim]:
        """Here we prepare all statements we normally
        would put on a unique separate page_reference item"""
        claims = []
        string_authors = self.__prepare_string_authors__(page_reference=page_reference)
        if string_authors:
            claims.extend(string_authors)
        string_editors = self.__prepare_string_editors__(page_reference=page_reference)
        if string_editors:
            claims.extend(string_editors)
        string_translators = self.__prepare_string_translators__(
            page_reference=page_reference
        )
        if string_translators:
            claims.extend(string_translators)
        archive_date = None
        archive_url = None
        publication_date = None
        title = None
        website_string = None
        if page_reference.access_date:
            access_date = datatypes.Time(
                prop_nr=self.wikibase.ACCESS_DATE,
                time=(
                    page_reference.access_date.replace(tzinfo=timezone.utc)
                    .replace(
                        hour=0,
                        minute=0,
                        second=0,
                    )
                    .strftime("+%Y-%m-%dT%H:%M:%SZ")
                ),
            )
        else:
            access_date = None
        if page_reference.archive_date:
            archive_date = datatypes.Time(
                prop_nr=self.wikibase.ARCHIVE_DATE,
                time=(
                    page_reference.archive_date.replace(tzinfo=timezone.utc)
                    .replace(
                        hour=0,
                        minute=0,
                        second=0,
                    )
                    .strftime("+%Y-%m-%dT%H:%M:%SZ")
                ),
            )
        else:
            access_date = None
        if page_reference.archive_url:
            archive_url = datatypes.URL(
                prop_nr=self.wikibase.ARCHIVE_URL,
                value=page_reference.archive_url,
            )
        if page_reference.publication_date:
            publication_date = datatypes.Time(
                prop_nr=self.wikibase.PUBLICATION_DATE,
                time=(
                    page_reference.publication_date.replace(tzinfo=timezone.utc)
                    .replace(
                        hour=0,
                        minute=0,
                        second=0,
                    )
                    .strftime("+%Y-%m-%dT%H:%M:%SZ")
                ),
            )
        if page_reference.title:
            title = datatypes.String(
                prop_nr=self.wikibase.TITLE,
                value=page_reference.title,
            )
        if page_reference.url:
            url = datatypes.URL(
                prop_nr=self.wikibase.URL,
                value=page_reference.url,
            )
        else:
            url = None
        if page_reference.website:
            website_string = datatypes.String(
                prop_nr=self.wikibase.WEBSITE_STRING,
                value=page_reference.website,
            )
        for claim in (
            access_date,
            archive_date,
            archive_url,
            publication_date,
            title,
            url,
            website_string,
        ):
            if claim:
                claims.append(claim)
        return claims

    @validate_arguments
    def __prepare_string_citations__(
        self, wikipedia_page  # type: WikipediaPage
    ) -> List[Claim]:
        # pseudo code
        # Return a citation for every page_reference that does not have a hash
        return [
            self.__prepare_string_citation__(page_reference=page_reference)
            for page_reference in (wikipedia_page.references or [])
            if not page_reference.has_hash
        ]

    @validate_arguments
    def prepare_and_upload_reference_item(
        self,
        page_reference: WikipediaPageReference,
        wikipedia_page,  # type: WikipediaPage
    ) -> str:
        """This method prepares and then tries to upload the reference to WikiCitations
        and returns the WCDQID either if successful upload or from the
        Wikibase error if an item with the exact same label/hash already exists.

        A possible speedup would be to only prepare the label and description
        and try to upload. If successful add all the statements to the item.
        This saves us from computing all the statements and discard them on error"""
        self.__prepare_reference_claim__(wikipedia_page=wikipedia_page)
        item = self.__prepare_new_reference_item__(
            page_reference=page_reference, wikipedia_page=wikipedia_page
        )
        wcdqid = self.__upload_new_item__(item=item)
        return wcdqid

    @validate_arguments
    def prepare_and_upload_website_item(
        self,
        page_reference: WikipediaPageReference,
        wikipedia_page,  # type: WikipediaPage
    ) -> str:
        self.__prepare_reference_claim__(wikipedia_page=wikipedia_page)
        item = self.__prepare_new_website_item__(
            page_reference=page_reference, wikipedia_page=wikipedia_page
        )
        wcdqid = self.__upload_new_item__(item=item)
        return wcdqid

    @validate_arguments
    def prepare_and_upload_wikipedia_page_item(
        self, wikipedia_page: Any
    ) -> Optional[str]:
        logging.debug("prepare_and_upload_wikipedia_page_item: Running")
        from wcdimportbot.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        if not isinstance(wikipedia_page, WikipediaPage):
            raise ValueError("did not get a WikipediaPage object")
        self.__prepare_reference_claim__(wikipedia_page=wikipedia_page)
        item = self.__prepare_new_wikipedia_page_item__(wikipedia_page=wikipedia_page)
        wcdqid = self.__upload_new_item__(item=item)
        return wcdqid

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __upload_new_item__(self, item: ItemEntity) -> str:
        """Upload the new item to WikiCitations"""
        if item is None:
            raise ValueError("Did not get what we need")
        if config.loglevel == logging.DEBUG:
            logger.debug("Finished item JSON")
            console.print(item.get_json())
        try:
            new_item = item.write(summary="New item imported from Wikipedia")
            print(f"Added new item {self.entity_url(new_item.id)}")
            if config.press_enter_to_continue:
                input("press enter to continue")
            logger.debug(f"returning new wcdqid: {new_item.id}")
            return str(new_item.id)
        except ModificationFailed as modification_failed:
            """Catch, extract and return the conflicting WCDQID"""
            logger.info(modification_failed)
            wcdqid = modification_failed.get_conflicting_entity_id
            if wcdqid is None:
                raise MissingInformationError("wcdqid was None")
            return str(wcdqid)
