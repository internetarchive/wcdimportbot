import logging
from os import getenv
from time import sleep
from unittest import TestCase

import pytest

import config
from src import WcdImportBot
from src.helpers import console
from src.models.wikibase.sandbox_wikibase import SandboxWikibase
from src.models.wikimedia.enums import WikimediaSite
from src.models.wikimedia.wikipedia.templates.english_wikipedia_page_reference import (
    EnglishWikipediaPageReference,
)

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class TestWikipediaPage(TestCase):
    def test_fix_dash(self):
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        page = WikipediaPage(
            wikibase=SandboxWikibase(),
            language_code="en",
            wikimedia_site=WikimediaSite.WIKIPEDIA,
        )
        page.__get_wikipedia_page_from_title__(title="Easter Island")
        page.__extract_and_parse_references__()
        logger.info(f"{len(page.references)} references found")
        for ref in page.references:
            if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
                # console.print(ref.template_name)
                if (
                    ref.url
                    == "http://www.ine.cl/canales/chile_estadistico/censos_poblacion_vivienda/censo_pobl_vivi.php"
                ):
                    console.print(ref.url, ref.archive_url)

    def test_fetch_page_data_and_parse_the_wikitext(self):
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        page = WikipediaPage(
            wikibase=SandboxWikibase(),
            language_code="en",
            wikimedia_site=WikimediaSite.WIKIPEDIA,
        )
        page.__fetch_page_data__(title="Test")
        assert page.page_id == 11089416
        assert page.title == "Test"

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_get_wcdqid_from_hash_via_sparql(self):
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        page = WikipediaPage(
            wikibase=SandboxWikibase(),
            language_code="en",
            wikimedia_site=WikimediaSite.WIKIPEDIA,
            title="Test",
        )
        # page.__fetch_page_data__(title="Test")
        page.extract_and_parse_and_upload_missing_items_to_wikibase()
        wcdqid = page.wikibase_return.item_qid
        console.print(
            f"Waiting {config.sparql_sync_waiting_time_in_seconds} seconds for WCDQS to sync"
        )
        sleep(config.sparql_sync_waiting_time_in_seconds)
        check_wcdqid = page.__get_wcdqid_from_hash_via_sparql__(md5hash=page.md5hash)
        print(wcdqid, check_wcdqid)
        assert wcdqid == check_wcdqid

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_compare_data_and_update_additional_reference(self):
        """First delete the test page, then upload it with one reference.
        Then"""
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        bot = WcdImportBot(wikibase=SandboxWikibase())
        bot.delete_one_page(title="Test")
        # exit()
        data = dict(
            url="https://archive.org/details/catalogueofshipw0000wils/",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wp = WikipediaPage(title="Test", wikibase=SandboxWikibase())
        wp.__fetch_page_data__()
        wp.__generate_hash__()
        wp.references.append(reference)
        wp.__upload_page_and_references__()
        # press_enter_to_continue()
        wp2 = WikipediaPage(title="Test", wikibase=SandboxWikibase())
        wp2.__fetch_page_data__()
        wp2.__generate_hash__()
        wp2.references.append(reference)
        data2 = dict(
            title="World War I",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        reference2 = EnglishWikipediaPageReference(**data2)
        reference2.wikibase = SandboxWikibase()
        reference2.finish_parsing_and_generate_hash()
        wp2.references.append(reference2)
        console.print(wp2.references)
        wp2.extract_and_parse_and_upload_missing_items_to_wikibase()

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_compare_data_and_update_removed_reference(self):
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        bot = WcdImportBot(wikibase=SandboxWikibase())
        bot.delete_one_page(title="Test")

        data = dict(
            url="https://archive.org/details/catalogueofshipw0000wils/",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wp = WikipediaPage(title="Test", wikibase=SandboxWikibase())
        wp.__fetch_page_data__()
        wp.__generate_hash__()
        wp.references.append(reference)
        wp.__upload_page_and_references__()
        # press_enter_to_continue()
        wp = WikipediaPage(title="Test", wikibase=SandboxWikibase())
        wp.__fetch_page_data__()
        wp.__generate_hash__()
        wp.extract_and_parse_and_upload_missing_items_to_wikibase()

    def test_compare_and_update_page(self):
        # TODO upload a test page with some statement
        # then update it with a page with one more statement
        pass
