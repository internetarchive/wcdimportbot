import logging
from os import getenv
from unittest import TestCase

import pytest

import config
from src.models.wikibase.crud import WikibaseCrud
from src.models.wikibase.crud.update import WikibaseCrudUpdate
from src.models.wikibase.enums import WriteRequired
from src.models.wikibase.sandbox_wikibase import SandboxWikibase
from src.models.wikibase.wikibase_return import WikibaseReturn
from src.models.wikimedia.wikipedia.templates.english_wikipedia_page_reference import (
    EnglishWikipediaPageReference,
)
from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class TestWikibaseCrudUpdate(TestCase):
    # def test_compare_and_update_claims_offline(self):
    #     old_data = dict(
    #         # oclc="test",
    #         url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
    #         template_name="cite book",
    #     )
    #     new_data = dict(
    #         oclc="test",
    #         url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
    #         template_name="cite book",
    #     )
    #     old_reference = EnglishWikipediaPageReference(**old_data)
    #     old_reference.wikibase = SandboxWikibase()
    #     old_reference.finish_parsing_and_generate_hash()
    #     new_reference = EnglishWikipediaPageReference(**new_data)
    #     new_reference.wikibase = SandboxWikibase()
    #     new_reference.finish_parsing_and_generate_hash()
    #     wppage = WikipediaPage(wikibase=SandboxWikibase())
    #     title = "Test"
    #     wppage.__get_wikipedia_page_from_title__(title=title)
    #     wppage.__generate_hash__()
    #     wcu = WikibaseCrudUpdate(wikibase=SandboxWikibase())
    #     wcu.compare_and_update_claims(
    #         entity=old_reference,
    #         wikipedia_page=wppage,
    #         wikibase_item=wcu.__prepare_new_reference_item__(
    #             page_reference=new_reference, wikipedia_page=wppage
    #         ),
    #     )

    def test_compare_claims_on_references(self):
        wikibase = SandboxWikibase()
        old_data = dict(
            # oclc="test",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        new_data = dict(
            oclc="test",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        old_reference = EnglishWikipediaPageReference(**old_data)
        old_reference.wikibase = wikibase
        old_reference.finish_parsing_and_generate_hash()
        new_reference = EnglishWikipediaPageReference(**new_data)
        new_reference.wikibase = wikibase
        new_reference.finish_parsing_and_generate_hash()
        new_reference.wikibase_return = WikibaseReturn(uploaded_now=False, item_qid="")
        wppage = WikipediaPage(wikibase=wikibase)
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        wcu = WikibaseCrudUpdate(wikibase=wikibase, testing=True, wikipedia_page=wppage)
        wcu.new_item = wcu.__prepare_new_reference_item__(
            page_reference=new_reference, wikipedia_page=wppage, testing=True
        )
        wcu.wikibase_item = wcu.__prepare_new_reference_item__(
            page_reference=old_reference, wikipedia_page=wppage, testing=True
        )
        # We expect 1 claims to be added but 2 in the list
        # because the hash is different after adding oclc because it is used for hashing
        # over self.url.
        assert WriteRequired.YES == wcu.compare_and_update_claims(
            entity=new_reference,
        )
        # console.print(claims_to_be_added)
        # assert len(claims_to_be_added) == 1
        # assert (
        #     claims_to_be_added[0].mainsnak.property_number
        #     == wikibase.OCLC_CONTROL_NUMBER
        # )
        # assert claims_to_be_added[0].mainsnak.datavalue["value"] == "test"

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_that_wbi_can_remove_claims(self):
        wikibase = SandboxWikibase()
        data = dict(
            # oclc="test",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = wikibase
        reference.finish_parsing_and_generate_hash()
        wppage = WikipediaPage(wikibase=wikibase)
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        wc = WikibaseCrud(wikibase=wikibase)
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        item.claims.remove(property=wikibase.HASH)
        with self.assertRaises(KeyError):
            item.claims.get(wikibase.HASH)
