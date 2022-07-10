from __future__ import annotations

import logging
from time import sleep
from typing import Dict, Iterable, Optional

from pydantic import validate_arguments
from wikibaseintegrator import (  # type: ignore
    WikibaseIntegrator,
    datatypes,
    wbi_config,
    wbi_login,
)
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import Qualifiers  # type: ignore
from wikibaseintegrator.models import References
from wikibaseintegrator.wbi_exceptions import (  # type: ignore
    ModificationFailed,
    NonExistentEntityError,
)
from wikibaseintegrator.wbi_helpers import delete_page  # type: ignore
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore

import config
from wcdimportbot.models.wikibase import Wikibase
from wcdimportbot.wcd_base_model import WcdBaseModel

logger = logging.getLogger(__name__)


class WikibaseCrud(WcdBaseModel):
    """This class models the WikiCitations Wikibase
    and handles all uploading to it

    We want to create items for all Wikipedia pages
    and references with a unique hash

    Terminology:
    page_reference is a reference that appear in a Wikipedia page
    reference_claim is a datastructure from WBI that contains the
    revision id and retrieved date of the statement

    The language code is the one used by Wikimedia Foundation"""

    language_code: str = "en"
    reference_claim: Optional[References]
    wikibase: Wikibase

    class Config:
        arbitrary_types_allowed = True

    @validate_arguments
    def __convert_wcd_entity_id_to_item_entity__(self, entity_id: str) -> ItemEntity:
        """Convert and get the item using WBI"""
        self.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator()
        return wbi.item.get(entity_id)

    @validate_arguments
    def __extract_item_ids__(self, sparql_result: Optional[Dict]) -> Iterable[str]:
        """Yield item ids from a sparql result"""
        if sparql_result:
            yielded = 0
            for binding in sparql_result["results"]["bindings"]:
                if item_id := self.__extract_wcdqs_json_entity_id__(data=binding):
                    yielded += 1
                    yield item_id
            if number_of_bindings := len(sparql_result["results"]["bindings"]):
                logger.info(f"Yielded {yielded} bindings out of {number_of_bindings}")

    @validate_arguments
    def __extract_wcdqs_json_entity_id__(
        self, data: Dict, sparql_variable: str = "item"
    ) -> str:
        """We default to "item" as sparql value because it is customary in the Wikibase ecosystem"""
        return str(
            data[sparql_variable]["value"].replace(self.wikibase.rdf_entity_prefix, "")
        )

    def __setup_wikibase_integrator_configuration__(
        self,
    ) -> None:
        wbi_config.config["USER_AGENT"] = "wcdimportbot"
        wbi_config.config["WIKIBASE_URL"] = self.wikibase.wikibase_url
        wbi_config.config["MEDIAWIKI_API_URL"] = self.wikibase.mediawiki_api_url
        wbi_config.config["MEDIAWIKI_INDEX_URL"] = self.wikibase.mediawiki_index_url
        wbi_config.config["SPARQL_ENDPOINT_URL"] = self.wikibase.sparql_endpoint_url

    @staticmethod
    def __wait_for_wcdqs_to_sync__():
        logger.info(
            f"Sleeping {config.sparql_sync_waiting_time_in_seconds} seconds for WCDQS to sync"
        )
        sleep(config.sparql_sync_waiting_time_in_seconds)

    @validate_arguments
    def entity_url(self, qid: str):
        return f"{self.wikibase.wikibase_url}/wiki/Item:{qid}"
