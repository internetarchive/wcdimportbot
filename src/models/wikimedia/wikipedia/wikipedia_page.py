from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from dateutil.parser import isoparse
from marshmallow.exceptions import ValidationError
from pydantic import validate_arguments

import config
from src.helpers import console
from src.helpers.template_extraction import extract_templates_and_params
from src.models.cache import Cache
from src.models.exceptions import MissingInformationError, WikibaseError
from src.models.wikibase import Wikibase
from src.models.wikibase.crud.create import WikibaseCrudCreate
from src.models.wikibase.crud.read import WikibaseCrudRead
from src.models.wikibase.crud.update import WikibaseCrudUpdate
from src.models.wikibase.wikibase_return import WikibaseReturn
from src.models.wikimedia.enums import WikimediaSite
from src.models.wikimedia.wikipedia.templates.english_wikipedia_page_reference import (
    EnglishWikipediaPageReferenceSchema,
)
from src.models.wikimedia.wikipedia.templates.wikipedia_page_reference import (
    WikipediaPageReference,
)
from src.wcd_base_model import WcdBaseModel

logger = logging.getLogger(__name__)


class WikipediaPage(WcdBaseModel):
    """Models a WMF Wikipedia page"""

    cache: Optional[Cache]
    language_code: str = "en"
    latest_revision_date: Optional[datetime]
    latest_revision_id: Optional[int]
    md5hash: Optional[str]
    page_id: Optional[int]
    references: List[WikipediaPageReference] = []
    title: Optional[str]
    wikibase_crud_create: Optional[WikibaseCrudCreate]
    wikibase_crud_read: Optional[WikibaseCrudRead]
    wikibase_crud_update: Optional[WikibaseCrudUpdate]
    wikibase_return: Optional[WikibaseReturn]
    wikimedia_event: Optional[
        Any  # We can't type this with WikimediaEvent because of pydantic
    ]
    wikimedia_site: WikimediaSite = WikimediaSite.WIKIPEDIA
    wikitext: Optional[str]
    wikibase: Wikibase

    class Config:
        arbitrary_types_allowed = True

    @property
    def absolute_url(self):
        return f"https://{self.language_code}.{self.wikimedia_site.value}.org/w/index.php?curid={self.page_id}"

    @property
    def number_of_hashed_references(self):
        return len(
            [
                reference
                for reference in self.references
                if reference.md5hash is not None
            ]
        )

    @property
    def number_of_references(self):
        return len(self.references)

    @property
    def percent_of_references_with_a_hash(self):
        if self.number_of_references == 0:
            return 0
        else:
            return int(
                self.number_of_hashed_references * 100 / self.number_of_references
            )

    @property
    def underscored_title(self):
        """Helper property"""
        if self.title is None:
            raise ValueError("self.title was None")
        return self.title.replace(" ", "_")

    @property
    def url(self):
        return (
            f"https://{self.language_code}.{self.wikimedia_site.value}.org/"
            f"wiki/{quote(self.underscored_title)}"
        )

    @property
    def wikibase_url(self):
        if self.wikibase.item_prefixed_wikibase:
            return f"{self.wikibase.wikibase_url}/wiki/Item:{self.wikibase_return.item_qid}"
        else:
            return f"{self.wikibase.wikibase_url}/wiki/{self.wikibase_return.item_qid}"

    def __calculate_hashed_template_distribution__(self):
        raise NotImplementedError("To be written")

    @validate_arguments
    def __check_and_upload_reference_item_to_wikibase_if_missing__(
        self, reference: WikipediaPageReference
    ) -> WikipediaPageReference:
        logger.debug(
            "__check_and_upload_reference_item_to_wikicitations_if_missing__: Running"
        )
        wcdqid = None
        if config.use_cache:
            wcdqid = self.__get_reference_wcdqid_from_cache__(reference=reference)
            if wcdqid:
                logger.debug(f"Got wcdqid:{wcdqid} from the cache")
                reference.wikibase_return = WikibaseReturn(
                    item_qid=wcdqid, uploaded_now=False
                )
            else:
                logger.info(
                    f"Could not find reference with {reference.md5hash} in the cache"
                )
                reference = (
                    self.__upload_reference_and_insert_in_the_cache_if_enabled__(
                        reference=reference
                    )
                )
        if wcdqid:
            # We got a WCDQID from the cache
            logger.debug(f"Got wcdqid:{wcdqid} from the cache/SPARQL")
            wikibase_return = WikibaseReturn(item_qid=wcdqid, uploaded_now=False)
            reference.wikibase_return = wikibase_return
        else:
            # We did not get a WCDQID, so try uploading
            reference = self.__upload_reference_and_insert_in_the_cache_if_enabled__(
                reference=reference
            )
        return reference

    @validate_arguments
    def __check_and_upload_website_item_to_wikibase_if_missing__(
        self, reference: WikipediaPageReference
    ):
        """This method checks if a website item is present
        using the first_level_domain_of_url_hash and the cache if
        enabled and uploads a new item if not"""
        if reference.first_level_domain_of_url_hash is None:
            raise ValueError("reference.first_level_domain_of_url_hash was None")
        logger.debug("Checking and uploading website item")
        if reference is None:
            raise ValueError("reference was None")
        if config.use_cache:
            wcdqid = self.__get_website_wcdqid_from_cache__(reference=reference)
            if wcdqid is not None:
                logger.debug(f"Got wcdqid:{wcdqid} from the cache")
                reference.first_level_domain_of_url_qid = wcdqid
        else:
            wcdqid = self.__get_wcdqid_from_hash_via_sparql__(
                md5hash=reference.first_level_domain_of_url_hash
            )
            reference.first_level_domain_of_url_qid = wcdqid
        if reference.first_level_domain_of_url_qid is None:
            reference = self.__upload_website_and_insert_in_the_cache_if_enabled__(
                reference=reference
            )
            logger.info(f"Added website item to WCD")
        else:
            logger.info(
                f"Added link to existing website item {reference.first_level_domain_of_url_qid}"
            )
        return reference

    def __compare_and_update_all_references__(self) -> None:
        """Compare and update all the references.
        We assume all references have already been uploaded to Wikibase"""
        logger.debug("__compare_and_update_all_references__: Running")
        if not self.references:
            console.print("No references found. Skipping comparison of references")
            # raise MissingInformationError("self.references was empty or None")
        else:
            self.__setup_wikibase_crud_update__()
            if self.wikibase_crud_update:
                count = 0
                total = len(self.references)
                for reference in self.references:
                    """We go through each reference in the object
                    and compare it to the existing one in Wikibase"""
                    count += 1
                    console.print(
                        f"Comparing reference {count}/{total} on page '{self.title}'"
                    )
                    self.wikibase_crud_update.compare_and_update_claims(
                        entity=reference
                    )
            else:
                raise WikibaseError()

    def __compare_and_update_page__(self):
        logger.debug("__compare_and_update_page__: Running")
        console.print(f"Comparing the page '{self.title}'")
        if not self.wikibase_return:
            raise MissingInformationError(
                "self.wikibase_return was None and is needed "
                "to judge whether to compare or not"
            )
        self.__setup_wikibase_crud_update__()
        self.wikibase_crud_update.compare_and_update_claims(entity=self)

    def __compare_data_and_update__(self):
        """We compare and update all references and the page data"""
        logger.debug("__compare_data_and_update__: Running")
        self.__compare_and_update_all_references__()
        self.__compare_and_update_page__()

    def __extract_and_parse_references__(self):
        logger.info("Extracting references now")
        # if self.wikimedia_event is not None:
        #     # raise ValueError("wikimedia_event was None")
        #     self.__get_title_from_event__()
        #     self.__get_wikipedia_page_from_event__()
        # elif self.title is not None:
        #     if self.pywikibot_site is None:
        #         raise ValueError("self.pywikibot_site was None")
        #     self.__get_wikipedia_page_from_title__()
        # else:
        self.__parse_templates__()
        self.__print_hash_statistics__()

    def __fetch_page_data__(self, title: str = "") -> None:
        """This fetches metadata and the latest revision id
        and date from the MediaWiki REST v1 API if needed"""
        # TODO refactor this into new class?
        logger.debug("__fetch_page_data__: Running")
        if (
            not self.latest_revision_id
            or not self.latest_revision_date
            or not self.wikitext
            or not self.page_id
        ):
            if not title and self.title:
                title = self.title
            elif not title and not self.title:
                raise MissingInformationError(
                    "Both self.title and title are empty or None"
                )
            else:
                self.title = title
            # This is needed to support e.g. https://en.wikipedia.org/wiki/Musk%C3%B6_naval_base
            title = title.replace(" ", "_")
            url = f"https://en.wikipedia.org/w/rest.php/v1/page/{title}"
            headers = {"User-Agent": config.user_agent}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # TODO read up on the documentation to find out if this is reliable
                self.latest_revision_id = int(data["latest"]["id"])
                self.latest_revision_date = isoparse(data["latest"]["timestamp"])
                self.page_id = int(data["id"])
                self.wikitext = data["source"]
            else:
                raise ValueError(
                    f"Could not fetch page data. Got {response.status_code} from {url}"
                )
        else:
            logger.debug(
                "Not fetching via REST API. We have already got all the data we need"
            )

    @staticmethod
    def __fix_class_key__(dictionary: Dict[str, Any]) -> Dict[str, Any]:
        """convert "class" key to "_class" to avoid collision with reserved python expression"""
        newdict = {}
        for key in dictionary:
            if key == "class":
                new_key = "news_class"
                newdict[new_key] = dictionary[key]
            else:
                newdict[key] = dictionary[key]
        return newdict

    @staticmethod
    def __fix_aliases__(dictionary: Dict[str, Any]) -> Dict[str, Any]:
        """Replace alias keys"""
        replacements = dict(
            accessdate="access_date",
            archiveurl="archive_url",
            archivedate="archive_date",
            ISBN="isbn",
            authorlink1="author_link1",
            authorlink2="author_link2",
            authorlink3="author_link3",
            authorlink4="author_link4",
            authorlink5="author_link5",
            authorlink="author_link",
        )
        newdict = {}
        for key in dictionary:
            replacement_made = False
            for replacement in replacements:
                if replacement == key:
                    new_key = replacements[key]
                    logger.debug(f"Replacing key {key} with {new_key}")
                    newdict[new_key] = dictionary[key]
                    replacement_made = True
            if not replacement_made:
                newdict[key] = dictionary[key]
        return newdict

    @staticmethod
    def __fix_dash__(dictionary: Dict[str, Any]) -> Dict[str, Any]:
        newdict = {}
        for key in dictionary:
            if "-" in key:
                new_key = key.replace("-", "_")
                newdict[new_key] = dictionary[key]
            else:
                newdict[key] = dictionary[key]
        return newdict

    @validate_arguments
    def __fix_keys__(self, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        dictionary = self.__fix_class_key__(dictionary=dictionary)
        dictionary = self.__fix_aliases__(dictionary=dictionary)
        return self.__fix_dash__(dictionary=dictionary)

    def __generate_hash__(self):
        """We generate a md5 hash of the page_reference as a unique identifier for any given page_reference in a Wikipedia page
        We choose md5 because it is fast https://www.geeksforgeeks.org/difference-between-md5-and-sha1/"""
        logger.debug(
            f"Generating hash based on: "
            f"{self.wikibase.title}{self.language_code}{self.page_id}"
        )
        if not self.page_id:
            raise MissingInformationError("self.page_id was None")
        self.md5hash = hashlib.md5(
            f"{self.wikibase.title}{self.language_code}{self.page_id}".encode()
        ).hexdigest()
        logger.debug(self.md5hash)

    @validate_arguments
    def __get_reference_wcdqid_from_cache__(
        self, reference: WikipediaPageReference
    ) -> Optional[str]:
        if self.cache is None:
            self.__setup_cache__()
        if self.cache is not None:
            wcdqid = self.cache.check_reference_and_get_wikibase_qid(
                reference=reference
            )
        else:
            raise ValueError("self.cache was None")
        logger.debug(f"result from the cache:{wcdqid}")
        return wcdqid

    @validate_arguments
    def __get_wcdqid_from_hash_via_sparql__(self, md5hash: str) -> Optional[str]:
        """Looks up the WCDQID in WikiCitaitons and returns
        it if only one found and complains if more than one was found"""
        logger.debug("__get_wcdqid_from_hash_via_sparql__: Running")
        logger.info(f"Looking up the WCDQID via SPARQL by searching for: {md5hash}")
        if self.wikibase_crud_read is None:
            self.wikibase_crud_read = WikibaseCrudRead(wikibase=self.wikibase)
        if self.wikibase_crud_read is not None:
            wcdqids = self.wikibase_crud_read.__get_wcdqids_from_hash__(md5hash=md5hash)
            if wcdqids is not None:
                if len(wcdqids) > 1:
                    raise ValueError(
                        "Got more than one WCDQID for a hash. This should never happen"
                    )
                elif len(wcdqids) == 1:
                    first_wcdqid = str(wcdqids[0])
                    logger.debug(f"Returning WCDQID {first_wcdqid}")
                    return first_wcdqid
            else:
                logger.debug("Got no match from SPARQL")
                return None
        else:
            raise ValueError("self.wikicitations was None")
        return None

    @validate_arguments
    def __get_website_wcdqid_from_cache__(
        self, reference: WikipediaPageReference
    ) -> Optional[str]:
        if self.cache is None:
            self.__setup_cache__()
        if self.cache is not None:
            wcdqid = self.cache.check_website_and_get_wikibase_qid(reference=reference)
        else:
            raise ValueError("self.cache was None")
        logger.debug(f"result from the cache:{wcdqid}")
        return wcdqid

    @validate_arguments
    def __get_wikipedia_page_from_title__(self, title: str):
        """Get the page from the Wikimedia site"""
        logger.info("Fetching the page data")
        self.__fetch_page_data__(title=title)

    @validate_arguments
    def __insert_reference_in_cache__(
        self, reference: WikipediaPageReference, wcdqid: str
    ):
        """Insert reference in the cache"""
        logger.debug("__insert_in_cache__: Running")
        if self.cache is None:
            self.__setup_cache__()
        if self.cache is not None:
            self.cache.add_reference(reference=reference, wcdqid=wcdqid)
        else:
            raise ValueError("self.cache was None")
        logger.info("Reference inserted into the hash database")

    @validate_arguments
    def __insert_website_in_cache__(
        self, reference: WikipediaPageReference, wcdqid: str
    ):
        logger.debug("__insert_website_in_cache__: Running")
        if self.cache is not None:
            self.cache.add_website(reference=reference, wcdqid=wcdqid)
        else:
            raise ValueError("self.cache was None")
        logger.info("Reference inserted into the hash database")

    def __page_has_already_been_uploaded__(self) -> bool:
        """This checks whether the page has already been uploaded by checking the cache"""
        console.print(f"Checking if the page '{self.title}' has already been uploaded")
        if config.use_cache:
            if self.cache is None:
                self.__setup_cache__()
            if self.cache is not None:
                wcdqid = self.cache.check_page_and_get_wikibase_qid(wikipedia_page=self)
            else:
                raise ValueError("self.cache was None")
            if wcdqid is None:
                logger.debug("Page not found in the cache")
                return False
            else:
                logger.debug("Page found in the cache")
                self.wikibase_return = WikibaseReturn(
                    item_qid=wcdqid, uploaded_now=False
                )
                return True
        else:
            if config.check_if_page_has_been_uploaded_via_sparql:
                logger.info("Not using the cache. Falling back to lookup via SPARQL")
                if self.md5hash is not None:
                    wcdqid = self.__get_wcdqid_from_hash_via_sparql__(
                        md5hash=self.md5hash
                    )
                else:
                    raise ValueError("self.md5hash was None")
                if wcdqid is not None:
                    self.wikibase_return = WikibaseReturn(
                        item_qid=wcdqid, uploaded_now=False
                    )
                    return True
                else:
                    return False
            else:
                logger.info("Skipping check if the page already exists")
                return False

    def __parse_templates__(self):
        """We parse all the templates into WikipediaPageReferences"""
        if self.wikitext is None:
            raise ValueError("self.wikitext was None")
        # We use the pywikibot template extracting function
        template_tuples = extract_templates_and_params(self.wikitext, True)
        number_of_templates = len(template_tuples)
        logger.info(
            f"Parsing {number_of_templates} templates from {self.title}, see {self.url}"
        )
        for template_name, content in template_tuples:
            # logger.debug(f"working on {template_name}")
            if template_name.lower() in config.supported_templates:
                parsed_template = self.__fix_keys__(json.loads(json.dumps(content)))
                parsed_template["template_name"] = template_name.lower()
                if config.loglevel == logging.DEBUG:
                    logger.debug("parsed_template:")
                    console.print(parsed_template)
                    # press_enter_to_continue()
                schema = EnglishWikipediaPageReferenceSchema()
                try:
                    reference: Optional[WikipediaPageReference] = schema.load(
                        parsed_template
                    )
                except ValidationError as error:
                    logger.debug(f"Validation error: {error}")
                    schema_log_file = "schema_errors.log"
                    self.__log_to_file__(message=str(error), file_name=schema_log_file)
                    logger.error(
                        f"This reference was skipped because an unknown "
                        f"field was found. See the file '{schema_log_file}' for details"
                    )
                    reference = None
                # DISABLED partial loading because it does not work :/
                # if not reference:
                #     logger.info("Trying now to deserialize the reference partially")
                #     # Load partially (ie. ignore the unknown field)
                #     reference: WikipediaPageReference = schema.load(
                #         parsed_template, partial=True
                #     )
                # if not reference:
                #     raise ValueError("This reference could not be deserialized. :/")
                # else:
                if reference:
                    reference.wikibase = self.wikibase
                    reference.finish_parsing_and_generate_hash()
                    # Handle duplicates:
                    if reference.md5hash in [
                        reference.md5hash
                        for reference in self.references
                        if reference.md5hash is not None
                    ]:
                        logging.debug(
                            "Skipping reference already present "
                            "in the list to avoid duplicates"
                        )
                    # if config.loglevel == logging.DEBUG:
                    #     console.print(reference.dict())
                    else:
                        self.references.append(reference)
            else:
                if config.debug_unsupported_templates:
                    logger.debug(f"Template '{template_name.lower()}' not supported")

    def __print_hash_statistics__(self):
        logger.info(
            f"Hashed {self.percent_of_references_with_a_hash} percent of "
            f"{len(self.references)} references on page {self.title}"
        )

    def __setup_cache__(self):
        self.cache = Cache()
        self.cache.connect()

    def __setup_wikibase_crud_create__(self):
        if not self.wikibase_crud_create:
            self.wikibase_crud_create = WikibaseCrudCreate(
                language_code=self.language_code,
                wikibase=self.wikibase,
            )

    def __setup_wikibase_crud_read__(self):
        if not self.wikibase_crud_read:
            self.wikibase_crud_read = WikibaseCrudRead(
                language_code=self.language_code,
                wikibase=self.wikibase,
            )

    def __setup_wikibase_crud_update__(self):
        if not self.wikibase_crud_update:
            self.wikibase_crud_update = WikibaseCrudUpdate(
                language_code=self.language_code,
                wikibase=self.wikibase,
            )
        self.wikibase_crud_update.wikipedia_page = self

    def __upload_page_and_references__(self):
        console.print(f"Importing page '{self.title}'")
        self.__setup_wikibase_crud_create__()
        self.wikibase_return = (
            self.wikibase_crud_create.prepare_and_upload_wikipedia_page_item(
                wikipedia_page=self,
            )
        )
        if config.use_cache:
            if self.wikibase_return is None:
                raise ValueError("wcdqid was None")
            self.cache.add_page(
                wikipedia_page=self, wcdqid=self.wikibase_return.item_qid
            )
        if self.wikibase_return.uploaded_now:
            console.print(
                f"Finished uploading {self.title} to Wikibase, "
                f"see {self.url} and {self.wikibase_url}"
            )
        else:
            console.print(
                f"{self.title} already exists in {self.wikibase.__repr_name__()}, "
                f"see {self.url} and {self.wikibase_url}"
            )
            raise ValueError("this should never happen")

    @validate_arguments
    def __upload_reference_to_wikibase__(
        self, reference: WikipediaPageReference
    ) -> WikibaseReturn:
        """This method tries to upload the reference to Wikibase
        and returns the WCDQID either if successful upload or from the
        Wikibase error if an item with the exact same label/hash already exists."""
        logger.debug("__upload_reference_to_wikicitations__: Running")
        if self.wikibase_crud_create is None:
            self.__setup_wikibase_crud_create__()
        if self.wikibase_crud_create:
            wikibase_return = (
                self.wikibase_crud_create.prepare_and_upload_reference_item(
                    page_reference=reference, wikipedia_page=self
                )
            )
            if wikibase_return:
                return wikibase_return
            else:
                raise MissingInformationError(
                    "Got None instead of WCDQID when trying to upload to Wikibase"
                )
        else:
            raise ValueError("self.wikibase_crud_create was None")

    @validate_arguments
    def __upload_reference_and_insert_in_the_cache_if_enabled__(
        self, reference: WikipediaPageReference
    ) -> WikipediaPageReference:
        # Here we get the reference back with WCDQID
        wikibase_return = self.__upload_reference_to_wikibase__(reference=reference)
        if config.use_cache:
            if not wikibase_return or not reference.md5hash:
                raise MissingInformationError("hash or WCDQID was None")
            self.__insert_reference_in_cache__(
                reference=reference, wcdqid=wikibase_return.item_qid
            )
        reference.wikibase_return = wikibase_return
        return reference

    @validate_arguments
    def __upload_website_to_wikibase__(
        self, reference: WikipediaPageReference
    ) -> WikibaseReturn:
        """This is a lower level method that only handles uploading the website item"""
        if self.wikibase_crud_create is None:
            self.__setup_wikibase_crud_create__()
        if self.wikibase_crud_create is not None:
            return self.wikibase_crud_create.prepare_and_upload_website_item(
                page_reference=reference, wikipedia_page=self
            )
        else:
            raise ValueError("self.wikicitations was None")

    @validate_arguments
    def __upload_website_and_insert_in_the_cache_if_enabled__(
        self, reference: WikipediaPageReference
    ) -> WikipediaPageReference:
        wikibase_return = self.__upload_website_to_wikibase__(reference=reference)
        wcdqid = wikibase_return.item_qid
        if config.use_cache:
            if wcdqid is None:
                raise ValueError("WCDQID was None")
            if reference.first_level_domain_of_url_hash is None:
                raise ValueError("first_level_domain_of_url_hash was None")
            logger.debug(
                f"Hash before insertion: {reference.first_level_domain_of_url_hash}. "
                f"WCDQID before insertion: {wcdqid}"
            )
            self.__insert_website_in_cache__(
                reference=reference,
                wcdqid=wcdqid,
            )
        reference.first_level_domain_of_url_qid = wcdqid
        return reference

    def __upload_references_and_websites_if_missing__(self):
        """Go through each reference and upload if missing to Wikibase"""
        logger.debug("__upload_references_and_websites_if_missing__: Running")
        updated_references = []
        count = 1
        total = len(self.references)
        for reference in self.references:
            console.print(f"Working on reference {count}/{total}")
            if reference.has_first_level_domain_url_hash:
                with console.status(
                    f"Linking to or uploading new website item for reference "
                    f"with link to {reference.first_level_domain_of_url}"
                ):
                    # Here we get the reference with the first_level_domain_of_url WCDQID back
                    reference = (
                        self.__check_and_upload_website_item_to_wikibase_if_missing__(
                            reference=reference
                        )
                    )
            if reference.has_hash:
                with console.status(f"Creating the reference item itself"):
                    # Here we get the reference with its own WCDQID back
                    reference = (
                        self.__check_and_upload_reference_item_to_wikibase_if_missing__(
                            reference=reference
                        )
                    )
            updated_references.append(reference)
            count += 1
        self.references = updated_references

    def extract_and_parse_and_upload_missing_items_to_wikibase(self) -> None:
        """Extract the references and upload first
        the references and then the page to Wikibase

        First we fetch the page data and generate the hash,
        then we setup the Wikibase and extract and parse
        the references.

        Then we upload the references and websites if missing
        and lastly we either upload the page or if missing
        compare and upload any missing claims."""
        logger.debug("extract_and_upload_to_wikibase: Running")
        self.__fetch_page_data__()
        self.__generate_hash__()
        self.__setup_wikibase_crud_create__()
        self.__extract_and_parse_references__()
        self.__upload_references_and_websites_if_missing__()
        if not self.__page_has_already_been_uploaded__():
            self.__upload_page_and_references__()
        else:
            self.__compare_data_and_update__()

    # def __get_title_from_event__(self):
    #     self.title = self.wikimedia_event.page_title
    #     if self.title is None or self.title == "":
    #         raise ValueError("title not set correctly")
    # def __find_references_without_hashes__(self):
    #     references_without_hashes = [
    #         page_reference for page_reference in self.references if page_reference.md5hash is None
    #     ]
    #     logger.info(f"references_without_hashes: {len(references_without_hashes)}")
    #     if references_without_hashes is None:
    #         self.references_without_hashes = []
    #     else:
    #         self.references_without_hashes = references_without_hashes
    #     self.number_of_references_without_a_hash = len(self.references_without_hashes)
    #     logger.info(
    #         f"number_of_references_without_a_hash: {self.number_of_references_without_a_hash}"
    #     )
    # def __get_wikipedia_page_from_event__(self):
    #     """Get the page from Wikipedia"""
    #     logger.info("Fetching the wikitext")
    #     self.pywikibot_page = pywikibot.Page(
    #         self.wikimedia_event.event_stream.pywikibot_site, self.title
    #     )
