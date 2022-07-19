import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import validate_arguments
from wikibaseintegrator import WikibaseIntegrator, wbi_login  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore

from src.models.exceptions import MissingInformationError
from src.models.wikibase.crud import WikibaseCrud

logger = logging.getLogger(__name__)


class WikibaseCrudRead(WikibaseCrud):
    """This models al reading of data from the Wikibase"""

    @property
    def number_of_pages(self):
        return self.__get_statistic__(
            property=self.wikibase.INSTANCE_OF, value=self.wikibase.WIKIPEDIA_PAGE
        )

    @property
    def number_of_references(self):
        return self.__get_statistic__(
            property=self.wikibase.INSTANCE_OF, value=self.wikibase.WIKIPEDIA_REFERENCE
        )

    @property
    def number_of_website_items(self):
        return self.__get_statistic__(
            property=self.wikibase.INSTANCE_OF, value=self.wikibase.WEBSITE_ITEM
        )

    @validate_arguments
    def __execute_query__(self, query: str):
        self.__setup_wikibase_integrator_configuration__()
        logger.debug(
            f"Trying to use this endpoint: {self.wikibase.sparql_endpoint_url}"
        )
        return execute_sparql_query(
            query=query, endpoint=self.wikibase.sparql_endpoint_url
        )

    @staticmethod
    def __extract_count_from_first_binding__(
        sparql_result: Dict[Any, Any]
    ) -> Optional[int]:
        """Get count from a sparql result"""
        logger.debug("__extract_count__: Running")
        sparql_variable = "count"
        if sparql_result:
            if sparql_result["results"] and sparql_result["results"]["bindings"]:
                first_binding = sparql_result["results"]["bindings"][0]
                return int(first_binding[sparql_variable]["value"])
            else:
                return None
        else:
            return None

    @validate_arguments
    def __get_all_items__(self, item_type: str) -> Iterable[str]:
        """Get all items of a certain type
        item_type must be a QID"""
        return self.__extract_item_ids__(
            sparql_result=self.__get_items_via_sparql__(
                f"""
                    prefix wcd: <{self.wikibase.rdf_prefix}/entity/>
                    prefix wcdt: <{self.wikibase.rdf_prefix}/prop/direct/>
                    SELECT ?item WHERE {{
                      ?item wcdt:{self.wikibase.INSTANCE_OF} wcd:{item_type}
                    }}
                    """
            )
        )

    def __get_all_items_and_hashes__(self) -> Iterable[Tuple[str, str]]:
        """Get all item qids and hashes"""
        logger.debug("__get_all_items_and_hashes__: Running")
        return self.__extract_item_ids_and_hashes__(
            sparql_result=self.__get_items_via_sparql__(
                f"""
                    prefix wcd: <{self.wikibase.rdf_prefix}/entity/>
                    prefix wcdt: <{self.wikibase.rdf_prefix}/prop/direct/>
                    SELECT ?item ?hash WHERE {{
                      VALUES ?values {{
                        wcd:{self.wikibase.WIKIPEDIA_PAGE}
                        wcd:{self.wikibase.WIKIPEDIA_REFERENCE}
                        wcd:{self.wikibase.WEBSITE_ITEM}
                      }}
                      ?item wcdt:{self.wikibase.INSTANCE_OF} ?values;
                            wcdt:{self.wikibase.HASH} ?hash.
                    }}
                    """
            )
        )

    @validate_arguments
    def __get_item_entity_from_wcdqs_json__(
        self, data: Dict, sparql_variable: str = "item"
    ) -> ItemEntity:
        return self.__convert_wcd_entity_id_to_item_entity__(
            self.__extract_wcdqs_json_entity_id__(
                data=data, sparql_variable=sparql_variable
            )
        )

    @validate_arguments
    def __get_items_via_sparql__(self, query: str) -> Any:
        """This is the lowest level function
        that executes the query with WBI after setting it up"""
        self.__setup_wikibase_integrator_configuration__()
        self.__wait_for_wcdqs_to_sync__()
        logger.debug(
            f"Trying to use this endpoint: {self.wikibase.sparql_endpoint_url}"
        )
        return execute_sparql_query(
            query=query, endpoint=self.wikibase.sparql_endpoint_url
        )

    @validate_arguments
    def __get_statistic__(self, property: str, value: str, prefix: bool = True):
        if prefix and (len(property) < 3 or len(value) < 3):
            raise ValueError("Either property or value was too short.")
        if prefix:
            query = f"""
            prefix wcd: <{self.wikibase.rdf_prefix}/entity/>
            prefix wcdt: <{self.wikibase.rdf_prefix}/prop/direct/>
                SELECT (COUNT(?item) as ?count) WHERE {{
                  ?item wcdt:{property} wcd:{value}.
                }}
            """
        else:
            query = f"""
            prefix wcd: <{self.wikibase.rdf_prefix}/entity/>
            prefix wcdt: <{self.wikibase.rdf_prefix}/prop/direct/>
                SELECT (COUNT(?item) as ?count) WHERE {{
                  ?item wcdt:{property} {value}.
                }}
            """
        return self.__extract_count_from_first_binding__(
            self.__execute_query__(query=query)
        )

    @validate_arguments
    def __get_wcdqids_from_hash__(self, md5hash: str) -> List[str]:
        """This is a slower SPARQL-powered fallback helper method
        used when config.use_cache is False"""
        logger.debug("__get_wcdqid_from_hash__: running")
        if not self.wikibase.HASH:
            raise MissingInformationError("self.wikibase.HASH was empty string")
        query = f"""
            prefix wcdt: <{self.wikibase.rdf_prefix}/prop/direct/>
            SELECT ?item WHERE {{
              ?item wcdt:{self.wikibase.HASH} "{md5hash}".
            }}
        """
        return list(
            self.__extract_item_ids__(
                sparql_result=self.__get_items_via_sparql__(query=query)
            )
        )

    @validate_arguments
    def get_external_identifier_statistic(self, property: str):
        return self.__get_statistic__(property=property, value="[]", prefix=False)

    @validate_arguments
    def get_item(self, item_id: str) -> Optional[ItemEntity]:
        """Get one item from WikiCitations"""
        self.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=self.wikibase.user_name, password=self.wikibase.botpassword
            ),
        )
        return wbi.item.get(item_id)
