from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import validate_arguments
from wikibaseintegrator import WikibaseIntegrator, wbi_login  # type: ignore
from wikibaseintegrator.datatypes import BaseDataType  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import Claim, Claims  # type: ignore
from wikibaseintegrator.wbi_enums import ActionIfExists  # type: ignore
from wikibaseintegrator.wbi_exceptions import ModificationFailed  # type: ignore

from src import console
from src.models.exceptions import DebugExit, MissingInformationError
from src.models.wikibase.crud import WikibaseCrud
from src.models.wikibase.crud.read import WikibaseCrudRead
from src.models.wikibase.enums import WriteRequired
from src.models.wikibase.properties import Properties
from src.models.wikimedia.wikipedia.templates.wikipedia_page_reference import (
    WikipediaPageReference,
)

logger = logging.getLogger(__name__)


class WikibaseCrudUpdate(WikibaseCrud):
    """This class handles all comparing and updating of Wikibase items

    entity: is the entity to compare. Either a WikipediaPage or a WikipediaPageReference
    new_item: new item based on fresh data from Wikpedia
    wikibase_item: current item in the Wikibase
    wikipedia_page: is the page the reference belongs to"""

    entity: Any  # Union["WikipediaPage", WikipediaPageReference],
    new_item: Optional[ItemEntity] = None
    testing: bool = False
    updated_claims: Claims = Claims()
    wikibase_item: Optional[ItemEntity] = None
    wikipedia_page: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def __compare_claims_and_upload__(
        self,
    ) -> WriteRequired:
        """We compare claims one by one and update the item in the end

        The algorithm for comparing is the __eq__ method in WBI which compares 3 qualities:
        1) property number
        2) datavalue
        3) qualifiers

        This comparison will never find/correct statements that refer to a deleted item.
        To fix those we need another approach.

        If we know which properties can have multiple values, then we can detect when
        a claim is outdated in all other properties like WEBSITE, etc."""
        if not self.new_item:
            raise MissingInformationError("self.new_item was None")
        if not self.wikibase_item:
            raise MissingInformationError("self.wikibase_item was None")
        with console.status("Comparing claims and uploading the result to Wikibase..."):
            from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

            if isinstance(self.entity, WikipediaPage):
                multiple_values_properties = [
                    self.wikibase.CITATIONS,
                    self.wikibase.STRING_CITATIONS,
                ]
                for new_claim in self.new_item.claims:
                    if new_claim not in self.wikibase_item.claims:
                        new_property_id = new_claim.mainsnak.property_number
                        # TODO fetch property_label to enable a better UI
                        # This means we might have an updated WEBSITE claim
                        if new_property_id not in multiple_values_properties:
                            self.__replace_single_value_property_claim__(
                                new_claim=new_claim
                            )
                        else:
                            # The property in question is a multi-value property and we simply add a new value
                            # and hope for the best.
                            logger.debug(
                                f"Adding missing claim on multi-value property {new_claim}"
                            )
                            self.updated_claims.add(new_claim)
            elif isinstance(self.entity, WikipediaPageReference):
                logger.debug("Going through reference claims")
                # There currently are no multi-value properties in use on references
                for new_claim in self.new_item.claims:
                    if new_claim not in self.wikibase_item.claims:
                        self.__replace_single_value_property_claim__(
                            new_claim=new_claim
                        )
                # debug check to see if we only have one website value left on P81
                website_claims = [
                    claim
                    for claim in self.updated_claims
                    if claim.mainsnak.property_number == self.wikibase.WEBSITE
                    and claim.removed is False
                ]
                if len(website_claims) > 1:
                    console.print(website_claims)
                    raise DebugExit()
            else:
                raise ValueError("Not a supported entity type")
            # Update the item with the updated claims
            self.wikibase_item.claims = self.updated_claims
            # self.__print_claim_statistics__()
            base_filter = []
            properties = Properties()
            property_names = properties.get_all_property_names()
            for name in property_names:
                base_filter.append(BaseDataType(prop_nr=getattr(self.wikibase, name)))
            # console.print(base_filter)
            write_required = self.wikibase_item.write_required(base_filter=base_filter)
            if write_required:
                if not self.testing:
                    self.__setup_wikibase_integrator_configuration__()
                    try:
                        self.wikibase_item.write(
                            summary=f"Updated the item based on changes in Wikipedia"
                        )
                        console.print(
                            f"Updated the item based on changes in Wikipedia, "
                            f"see {self.wikibase.entity_history_url(item_id=self.wikibase_item.id)}"
                        )
                        return WriteRequired.YES
                    except ModificationFailed as e:
                        message = (
                            f"The {self.entity.__repr_name__()} item {self.wikibase_item.id} "
                            f"could not be updated because of this error: {e}"
                        )
                        logger.error(message)
                        self.__log_to_file__(
                            message=message, file_name="update-failed.log"
                        )
                        raise DebugExit()
                else:
                    console.print(
                        "Write required but skipping because of testing was True"
                    )
                    return WriteRequired.YES
            else:
                console.print("No write required according to WikibaseIntegrator")
                return WriteRequired.NO

    # def __print_claim_statistics__(self):
    #     """We print the statistics of all the claims"""
    #     pass
    #     # current_property_numbers = {
    #     #     claim.mainsnak.property_number for claim in wikibase_item.claims
    #     # }
    #     # logger.info(
    #     #     f"Found these property numbers {current_property_numbers} in the item in Wikibase"
    #     # )
    #     # new_property_numbers = {
    #     #     claim.mainsnak.property_number for claim in new_item.claims
    #     # }
    #     # logger.info(
    #     #     f"Found these property numbers {new_property_numbers} on the newly prepared item"
    #     # )

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __replace_single_value_property_claim__(self, new_claim: Claim):
        """This method replaces a claim on a single-value property"""
        logger.debug("__replace_single_value_property_claim__: Running")
        if not self.wikibase_item:
            raise MissingInformationError("self.wikibase_item was None")
        new_property_id = new_claim.mainsnak.property_number
        # The new claim should replace the current one since it is a single value property.
        current_claims = [
            claim
            for claim in self.wikibase_item.claims
            if claim.mainsnak.property_number == new_property_id
        ]
        logger.info(
            f"Found {len(current_claims)} single value "
            f"claims to remove with property {new_property_id}."
        )
        # If REPLACE_ALL works as it is supposed the following should not be neccessary:
        for claim in current_claims:
            logger.debug(f"Removing existing claim on single-value property {claim}")
            claim.remove()
            if not claim.removed:
                logger.error("Removed claim without removed=True, this is a bug")
                console.print(claim)
                raise DebugExit()
            self.updated_claims.add(claim)
        # The old claims have now been designated for removal.
        # Now we add the new claim.
        logger.debug(f"Adding missing claim on single-value property {new_claim}")
        self.updated_claims.add(new_claim, action_if_exists=ActionIfExists.REPLACE_ALL)

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def compare_and_update_claims(self, entity=Any) -> WriteRequired:
        """We compare and update claims that are completely missing from the Wikibase item.
        We also remove reference claims no longer present in the Wikipedia page."""
        logger.debug("compare_and_update_claims: Running")
        self.entity = entity
        # We reset this to avoid polution-bugs.
        self.updated_claims = Claims()
        if not self.wikipedia_page:
            raise MissingInformationError("self.wikipedia_page was None")
        if not self.entity.wikibase_return:
            raise MissingInformationError("new_reference.wikibase_return was None")
        if self.entity.wikibase_return.uploaded_now:
            logger.info("Skipping comparison because the reference was just uploaded")
            return WriteRequired.NO
        else:
            self.__fetch_and_prepare_data_for_comparison__()
            return self.__compare_claims_and_upload__()

    def __fetch_and_prepare_data_for_comparison__(self):
        """Fetch and prepare the information needed to perform a comparison"""
        logger.debug("__fetch_and_prepare_data_for_comparison__: Running")
        wcr = WikibaseCrudRead(wikibase=self.wikibase)
        if isinstance(self.entity, WikipediaPageReference):
            if self.entity.title:
                console.print(
                    f"Comparing {self.entity.template_name} "
                    f"reference with the title '{self.entity.title}'"
                )
            else:
                console.print(
                    f"Comparing {self.entity.template_name} "
                    f"reference with missing title"
                )
            logger.info(
                f"See {self.wikibase.entity_url(item_id=self.entity.wikibase_return.item_qid)}"
            )
            self.new_item = wcr.__prepare_new_reference_item__(
                page_reference=self.entity, wikipedia_page=self.wikipedia_page
            )
        else:
            logger.info(f"Comparing page with title '{self.entity.title}")
            self.new_item = wcr.__prepare_new_wikipedia_page_item__(
                wikipedia_page=self.entity
            )
        if not self.testing:
            # We always overwrite the item if not testing
            self.wikibase_item = wcr.get_item(
                item_id=self.entity.wikibase_return.item_qid
            )
            if not self.wikibase_item:
                raise ValueError(
                    "Cannot compare because the "
                    "item was not found in the Wikibase. "
                    "This should never happen."
                )
        else:
            if not self.wikibase_item:
                raise ValueError(
                    "Cannot compare because the " "wikibase_item was not set"
                )
