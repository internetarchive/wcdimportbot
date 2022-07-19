import logging
from unittest import TestCase

from requests import HTTPError

import config
from src.models.wikibase.crud.read import WikibaseCrudRead
from src.models.wikibase.sandbox_wikibase import SandboxWikibase

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class TestWikibaseCrudRead(TestCase):
    def test_get_items_via_sparql(self):
        wc = WikibaseCrudRead(wikibase=SandboxWikibase())
        with self.assertRaises(HTTPError):
            wc.__get_items_via_sparql__(query="test")

    def test_get_all_items_and_hashes(self):
        wc = WikibaseCrudRead(wikibase=SandboxWikibase())
        result = wc.__get_all_items_and_hashes__()
        count = 0
        for entry in result:
            count += 1
            print(entry)
            if count >= 10:
                break
