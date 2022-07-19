"""
The purpose of this script is to setup all the properties we want in a new Wikibase
This could be fully automated but we don't need it often enough for it to be feasible
e.g. using a json file on disk which is read every time the bot runs.
We keep it simple and using a class will enable typing for the developer which is
a big plus :)
"""
import argparse
import logging
from typing import Any, Dict, List

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_login  # type: ignore
from wikibaseintegrator.entities import ItemEntity  # type: ignore
from wikibaseintegrator.models import (  # type: ignore
    Claims,
    Descriptions,
    Labels,
    LanguageValue,
)
from wikibaseintegrator.wbi_enums import WikibaseDatatype  # type: ignore
from wikibaseintegrator.wbi_exceptions import MWApiError  # type: ignore

import config
from src import Wikibase, console
from src.models.wikibase.crud import WikibaseCrud
from src.models.wikibase.dictionaries import wcd_archive_items, wcd_items
from src.models.wikibase.properties import Properties
from src.models.wikibase.sandbox_wikibase import SandboxWikibase

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class SetupNewWikibase(BaseModel):
    wikibase: Wikibase = SandboxWikibase()

    def __setup_archive_items__(self) -> List[str]:
        # They rely on each other so they have to be created in a certain order it seems
        # then the instance_of=archive item
        output_text = []
        wc = WikibaseCrud(wikibase=self.wikibase)
        wc.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=wc.wikibase.user_name,
                password=wc.wikibase.botpassword,
                mediawiki_api_url=wc.wikibase.mediawiki_api_url,
            )
        )
        archive_label = "Archive"
        archive_description = "web archive"
        archive_item = wbi.item.new(
            labels=Labels().add(
                language_value=LanguageValue(language="en", value=archive_label)
            ),
            descriptions=Descriptions().add(
                language_value=LanguageValue(language="en", value=archive_description)
            ),
        )
        try:
            result = archive_item.write()
            archive_item_qid = result.id
            output_text.append(
                f'ARCHIVE_ITEM = "{archive_item_qid}" # '
                f"label: {archive_label} "
                f"description: {archive_description}"
            )
        except MWApiError as e:
            archive_item_qid = e.get_conflicting_entity_ids[0]
            existing_archive_item = wbi.item.get(entity_id=archive_item_qid)
            output_text.append(
                f'ARCHIVE_ITEM = "{existing_archive_item.id}" # '
                f'label: {existing_archive_item.labels.get(language="en")} '
                f'description: {existing_archive_item.descriptions.get(language="en")}'
            )
            # logger.error(f"Got error: {e} from the Wikibase")
        # then the individual archive organization items
        console.print(f"Setting up {len(wcd_archive_items)} archive items")
        count = 1
        for item in wcd_archive_items:
            if count <= 50:
                data: Dict[Any, Any] = wcd_archive_items[item]
                description = data["description"]
                label = data["label"]
                draft_item = wbi.item.new(
                    labels=Labels().add(
                        language_value=LanguageValue(language="en", value=label)
                    ),
                    descriptions=Descriptions().add(
                        language_value=LanguageValue(language="en", value=description)
                    ),
                    # add claim to individual archive organization items
                    claims=Claims().add(
                        claims=[
                            # instance of
                            datatypes.Item(
                                prop_nr=self.wikibase.INSTANCE_OF,
                                value=archive_item_qid,
                            )
                        ]
                    ),
                )
                try:
                    new_item = draft_item.write()
                    output_text.append(
                        f'{item} = "{new_item.id}" # label: {label} description: {description}'
                    )
                except MWApiError as e:
                    existing_item_qid = e.get_conflicting_entity_ids[0]
                    existing_item = wbi.item.get(entity_id=existing_item_qid)
                    output_text.append(
                        f'{item} = "{existing_item.id}" # label: '
                        f'{existing_item.labels.get(language="en")} description: '
                        f'{existing_item.descriptions.get(language="en")}'
                    )
                    # logger.error(f"Got error: {e} from the Wikibase")
                count += 1
        return output_text

    @staticmethod
    def __setup_argparse_and_return_args__() -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-i",
            "--items",
            action="store_true",
            help="Import the semantic items we need",
        )
        parser.add_argument(
            "-p",
            "--properties",
            action="store_true",
            help="Import the properties we need",
        )
        return parser.parse_args()

    def __setup_other_items__(self) -> List[str]:
        # first create the wikipedia items
        output_text = []
        wc = WikibaseCrud(wikibase=self.wikibase)
        wc.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=wc.wikibase.user_name,
                password=wc.wikibase.botpassword,
                mediawiki_api_url=wc.wikibase.mediawiki_api_url,
            )
        )
        console.print(f"Setting up {len(wcd_items)} other items")
        count = 1
        for item in wcd_items:
            if count <= 50:
                data: Dict[Any, Any] = wcd_items[item]
                description = data["description"]
                label = data["label"]
                draft_item = wbi.item.new(
                    labels=Labels().add(
                        language_value=LanguageValue(language="en", value=label)
                    ),
                    descriptions=Descriptions().add(
                        language_value=LanguageValue(language="en", value=description)
                    ),
                )
                try:
                    new_item = draft_item.write()
                    output_text.append(
                        f'{item} = "{new_item.id}" # label: {label} description: {description}'
                    )
                except MWApiError as e:
                    existing_item_qid = e.get_conflicting_entity_ids[0]
                    existing_item = wbi.item.get(entity_id=existing_item_qid)
                    output_text.append(
                        f'{item} = "{existing_item.id}" # label: '
                        f'{existing_item.labels.get(language="en")} description: '
                        f'{existing_item.descriptions.get(language="en")}'
                    )
                    # logger.error(f"Got error: {e} from the Wikibase")
                count += 1
        return output_text

    def run(self):
        args = self.__setup_argparse_and_return_args__()
        if args.items is True:
            self.setup_items()
        if args.properties is True:
            self.setup_properties()
        console.print(
            f"Now copy the above output into the {snw.wikibase.__repr_name__()} "
            f"class."
        )

    def setup_items(self):
        if not self.wikibase.INSTANCE_OF:
            raise ValueError(
                "Please setup the properties first before setting up the items. See -h"
            )
        output_text = self.__setup_other_items__()
        output_text.extend(self.__setup_archive_items__())
        for line in output_text:
            print(line)

    def setup_properties(self):
        # iterate over the dictionary and create all the properties
        # output in a form that can be copy-pasted into a Wikibase class
        # (ie 'author = "P1"\nauthor_name_string = "P2"'
        wc = WikibaseCrud(wikibase=self.wikibase)
        wc.__setup_wikibase_integrator_configuration__()
        wbi = WikibaseIntegrator(
            login=wbi_login.Login(
                user=wc.wikibase.user_name,
                password=wc.wikibase.botpassword,
                mediawiki_api_url=wc.wikibase.mediawiki_api_url,
            )
        )
        output_text = []
        properties = Properties()
        console.print(f"Setting up {len(properties.properties)} properties")
        count = 1
        for entry in properties.properties:
            if count <= 150:
                data: Dict[Any, Any] = properties.properties[entry]
                datatype: WikibaseDatatype = data["datatype"]
                description = data["description"]
                label = entry.replace("_", " ").title()
                draft_property = wbi.property.new(
                    datatype=datatype.value,
                    labels=Labels().add(
                        language_value=LanguageValue(language="en", value=label)
                    ),
                    descriptions=Descriptions().add(
                        language_value=LanguageValue(language="en", value=description)
                    ),
                )
                try:
                    logger.info(f"Trying to create {label}")
                    property = draft_property.write()
                    output_text.append(
                        f'{entry} = "{property.id}" # datatype: {datatype} description: {description}'
                    )
                except MWApiError as e:
                    existing_property = e.get_conflicting_entity_ids[0]
                    property = wbi.property.get(entity_id=existing_property)
                    output_text.append(
                        f'{entry} = "{property.id}" # datatype: {datatype} description: {property.descriptions.get(language="en")}'
                    )
                    # logger.warning(f"Got error: {e} from the Wikibase")
                count += 1
        if len(output_text) != len(properties.properties):
            raise ValueError("Could not setup all properties.")
        else:
            # console.print(output_text)
            for line in output_text:
                print(line)


if __name__ == "__main__":
    console.print("First setup the properties and then the items. Use -h to see help.")
    snw = SetupNewWikibase()
    snw.run()
