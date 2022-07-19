import logging

from pydantic import validate_arguments
from wikibaseintegrator import wbi_login  # type: ignore
from wikibaseintegrator.wbi_exceptions import NonExistentEntityError  # type: ignore
from wikibaseintegrator.wbi_helpers import delete_page  # type: ignore

import config
from src.helpers import console, press_enter_to_continue
from src.models.wikibase.crud import WikibaseCrud
from src.models.wikibase.crud.read import WikibaseCrudRead
from src.models.wikibase.enums import Result, SupportedItemType

logger = logging.getLogger(__name__)


class WikibaseCrudDelete(WikibaseCrud):
    @validate_arguments
    def __delete_items__(self, item_type: SupportedItemType):
        """Delete items of by type one by one
        Wikibase is currently lacking an API to mass delete"""
        read = WikibaseCrudRead(wikibase=self.wikibase)
        items = (
            read.__get_all_items__(item_type=getattr(self.wikibase, item_type.name))
            or []
        )
        if items:
            self.__setup_wikibase_integrator_configuration__()
            with console.status(f"Deleting all {item_type.name.title()} items"):
                count = 0
                for item_id in items:
                    logger.info(f"Deleting {item_id}")
                    self.__delete_item__(item_id=item_id)
                    # logger.debug(result)
                    if config.press_enter_to_continue:
                        press_enter_to_continue()
                    count += 1
                console.print(f"Done deleting a total of {count} items")
        else:
            console.print(
                f"Got no {item_type.name.title()} items from the WCD Query Service."
            )

    @validate_arguments
    def __delete_item__(self, item_id: str) -> Result:
        if config.press_enter_to_continue:
            input(f"Do you want to delete {item_id}?")
        logger.debug(f"trying to log in to the wikibase as {self.wikibase.user_name}")
        self.__setup_wikibase_integrator_configuration__()
        try:
            result = delete_page(
                title=f"Item:{item_id}",
                # deletetalk=True,
                login=wbi_login.Login(
                    user=self.wikibase.user_name,
                    password=self.wikibase.botpassword,
                    mediawiki_api_url=self.wikibase.mediawiki_api_url,
                ),
            )
            console.print(result)
            if result:
                return Result.SUCCESSFUL
            else:
                return Result.FAILED
        except NonExistentEntityError:
            return Result.FAILED

    def delete_imported_items(self):
        """This function deletes all the imported items in WikiCitations"""
        console.print("Deleting all imported items")
        self.__delete_items__(item_type=SupportedItemType.WIKIPEDIA_PAGE)
        self.__delete_items__(item_type=SupportedItemType.WIKIPEDIA_PAGE)
        self.__delete_items__(item_type=SupportedItemType.WEBSITE_ITEM)
