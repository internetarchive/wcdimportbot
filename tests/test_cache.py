import logging
from typing import List
from unittest import TestCase

import config
from src import WcdImportBot, Cache, console
from src.models.wikimedia.wikipedia.templates.wikipedia_page_reference import (
    WikipediaPageReference,
)

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class TestCache(TestCase):
    # def test_initialize(self):
    #     database = Cache()
    #     database.connect()
    #     database.initialize()
    #     # self.fail()
    #
    # def test_drop(self):
    #     database = Cache()
    #     database.connect()
    #     database.drop()
    #     # self.fail()

    def test_add_reference(self):
        config.use_cache = True
        bot = WcdImportBot()
        bot.get_page_by_title(
            title="!Action Pact!",
        )
        [
            page.__parse_templates__(check_and_upload_to_cache=False)
            for page in bot.pages
        ]
        bot.print_statistics()
        pages = [page for page in bot.pages]
        references: List[WikipediaPageReference] = []
        for page in pages:
            if len(page.references) > 0:
                references.extend(page.references)
        hashed_references = [reference for reference in references if reference.md5hash]
        if len(hashed_references) > 0:
            logger.info(f"found {len(hashed_references)} hashed references")
            reference = hashed_references[0]
            reference.wikicitations_qid = "test"
            console.print(reference)
            cache = Cache()
            cache.connect()
            cache.add_reference(reference=reference)
            check = cache.check_reference_and_get_wikicitations_qid(reference=reference)
            print(f"check:{check}")
            # assert check is not None
            assert check == "test"
        else:
            raise ValueError("No hashed references found")
            # self.fail()