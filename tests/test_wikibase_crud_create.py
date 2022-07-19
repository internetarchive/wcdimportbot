import logging
from os import getenv
from typing import List
from unittest import TestCase

import pytest
from wikibaseintegrator.models import Claim  # type: ignore

import config
from src import SandboxWikibase, console
from src.models.wikibase.crud import WikibaseCrud
from src.models.wikibase.crud.create import WikibaseCrudCreate
from src.models.wikibase.wikibase_return import WikibaseReturn
from src.models.wikimedia.wikipedia.templates.english_wikipedia_page_reference import (
    EnglishWikipediaPageReference,
)
from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class TestWikibaseCrudCreate(TestCase):
    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_prepare_new_reference_item(self):
        wc = WikibaseCrud(wikibase=SandboxWikibase())
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        wppage.__get_wikipedia_page_from_title__(title="Democracy")
        reference = EnglishWikipediaPageReference(
            **{
                "last": "Tangian",
                "first": "Andranik",
                "date": "2020",
                "title": "Analytical Theory of Democracy: History, Mathematics and Applications",
                "series": "Studies in Choice and Welfare",
                "publisher": "Springer",
                "location": "Cham, Switzerland",
                "isbn": "978-3-030-39690-9",
                "doi": "10.1007/978-3-030-39691-6",
                "s2cid": "216190330",
                "template_name": "cite book",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        assert len(reference.persons_without_role) > 0
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        console.print(item.get_json())
        assert item.claims.get(property=wc.wikibase.FULL_NAME_STRING) is not None

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_prepare_new_reference_item_with_very_long_title(self):
        wc = WikibaseCrud(wikibase=SandboxWikibase())
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        wppage.__get_wikipedia_page_from_title__(title="Test")
        reference = EnglishWikipediaPageReference(
            **{
                "last": "Tangian",
                "first": "Andranik",
                "date": "2020",
                "title": (
                    "Analytical Theory of Democracy: "
                    "History, Mathematics and Applications Analytical "
                    "Theory of Democracy: History, "
                    "Mathematics and Applications Analytical Theory of "
                    "Theory of Democracy: History, "
                    "Mathematics and Applications Analytical Theory of "
                    "Democracy: History, Mathematics and Applications"
                ),
                "series": "Studies in Choice and Welfare",
                "publisher": "Springer",
                "location": "Cham, Switzerland",
                "isbn": "978-3-030-39690-9",
                "doi": "10.1007/978-3-030-39691-6",
                "s2cid": "216190330",
                "template_name": "cite book",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        # console.print(item.get_json())
        assert len(item.labels.get(language="en")) == 250

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_prepare_new_wikipedia_page_item_invalid_qid(self):
        wc = WikibaseCrud(wikibase=SandboxWikibase())
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        wppage.__get_wikipedia_page_from_title__(title="Democracy")
        reference = EnglishWikipediaPageReference(
            **{
                "last": "Tangian",
                "first": "Andranik",
                "date": "2020",
                "title": "Analytical Theory of Democracy: History, Mathematics and Applications",
                "series": "Studies in Choice and Welfare",
                "publisher": "Springer",
                "location": "Cham, Switzerland",
                "isbn": "978-3-030-39690-9",
                "doi": "10.1007/978-3-030-39691-6",
                "s2cid": "216190330",
                "template_name": "cite book",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        reference.wikibase_return = WikibaseReturn(item_qid="test", uploaded_now=False)
        wppage.references = []
        wppage.references.append(reference)
        with self.assertRaises(ValueError):
            wc.max_number_of_item_citations = 0
            wc.__prepare_new_wikipedia_page_item__(
                wikipedia_page=wppage,
            )
        # console.print(item.get_json())

        # logger.info(f"url: {wppage.wikicitations_url}")

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_prepare_new_wikipedia_page_item_valid_qid(self):
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Democracy"
        wppage.__get_wikipedia_page_from_title__(title=title)
        reference = EnglishWikipediaPageReference(
            **{
                "last": "Tangian",
                "first": "Andranik",
                "date": "2020",
                "title": "Analytical Theory of Democracy: History, Mathematics and Applications",
                "series": "Studies in Choice and Welfare",
                "publisher": "Springer",
                "location": "Cham, Switzerland",
                "isbn": "978-3-030-39690-9",
                "doi": "10.1007/978-3-030-39691-6",
                "s2cid": "216190330",
                "template_name": "cite book",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        reference.wikibase_return = WikibaseReturn(item_qid="Q1", uploaded_now=False)
        wppage.references = []
        wppage.references.append(reference)
        wppage.__generate_hash__()
        # with self.assertRaises(ValueError):
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        item = wc.__prepare_new_wikipedia_page_item__(
            wikipedia_page=wppage,
        )
        # console.print(item.get_json())
        # assert item.labels.get("en") == title
        citations: List[Claim] = item.claims.get(wc.wikibase.CITATIONS)
        # console.print(citations[0].mainsnak.datavalue["value"]["id"])
        assert citations[0].mainsnak.datavalue["value"]["id"] == "Q1"
        # logger.info(f"url: {wppage.wikicitations_url}")

    # @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    # def test_prepare_and_upload_wikipedia_page_item_valid_qid(self):
    #     wppage = WikipediaPage(wikibase=SandboxWikibase())
    #     title = "Democracy"
    #     wppage.__get_wikipedia_page_from_title__(title=title)
    #     wppage.__generate_hash__()
    #     reference = EnglishWikipediaPageReference(
    #         **{
    #             "last": "Tangian",
    #             "first": "Andranik",
    #             "date": "2020",
    #             "title": "Analytical Theory of Democracy: History, Mathematics and Applications",
    #             "series": "Studies in Choice and Welfare",
    #             "publisher": "Springer",
    #             "location": "Cham, Switzerland",
    #             "isbn": "978-3-030-39690-9",
    #             "doi": "10.1007/978-3-030-39691-6",
    #             "s2cid": "216190330",
    #             "template_name": "cite book",
    #         }
    #     )
    #     reference.finish_parsing_and_generate_hash()
    #     test_qid = "Q4"
    #     reference.wikicitations_qid = test_qid
    #     wppage.references = []
    #     wppage.references.append(reference)
    #     wikibase = SandboxWikibase()
    #     wcr = WikibaseCrudRead(wikibase=wikibase)
    #     wcr.prepare_and_upload_wikipedia_page_item(
    #         wikipedia_page=wppage,
    #     )
    #     items = wcr.__get_all_items__(item_type=wikibase.WIKIPEDIA_PAGE)
    #     assert items and len(items) == 1

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_prepare_and_upload_website_item(self):
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Democracy"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        # This reference is the first one on https://en.wikipedia.org/w/index.php?title=Democracy&action=edit
        reference = EnglishWikipediaPageReference(
            **{
                "agency": "Oxford University Press",
                "access-date": "24 February 2021",
                "title": "Democracy",
                "template_name": "cite news",
                "url": "https://www.oxfordreference.com/view/10.1093/acref/9780195148909.001.0001/acref-9780195148909-e-241",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wcdqid = wc.prepare_and_upload_website_item(
            page_reference=reference, wikipedia_page=wppage
        )
        assert wcdqid is not None
        # bot = WcdImportBot(wikibase=SandboxWikibase())
        # bot.rinse_all_items_and_cache()

    # @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    # def test_uploading_a_page_reference_and_website_item(self):
    #     # wcd = WikibaseCrudDelete(wikibase=SandboxWikibase())
    #     # wcd.delete_imported_items()
    #     wppage = WikipediaPage(wikibase=SandboxWikibase())
    #     title = "Democracy"
    #     wppage.__get_wikipedia_page_from_title__(title=title)
    #     wppage.__generate_hash__()
    #     # This reference is the first one on https://en.wikipedia.org/w/index.php?title=Democracy&action=edit
    #     reference = EnglishWikipediaPageReference(
    #         **{
    #             "agency": "Oxford University Press",
    #             "access-date": "24 February 2021",
    #             "title": "Democracy",
    #             "template_name": "cite news",
    #             "url": "https://www.oxfordreference.com/view/10.1093/acref/9780195148909.001.0001/acref-9780195148909-e-241",
    #         }
    #     )
    #     reference.wikibase = SandboxWikibase()
    #     reference.finish_parsing_and_generate_hash()
    #     wppage.references = []
    #     wppage.references.append(reference)
    #     wppage.__upload_references_and_websites_if_missing__()
    #     console.print(
    #         f"Waiting {config.sparql_sync_waiting_time_in_seconds} seconds for WCDQS to sync"
    #     )
    #     sleep(config.sparql_sync_waiting_time_in_seconds)
    #     wcr = WikibaseCrudRead(wikibase=SandboxWikibase())
    #     items = wcr.__get_all_items__(item_type=SandboxWikibase().WEBSITE_ITEM)
    #     assert len(items) == 1
    #     ref_items = wcr.__get_all_items__(
    #         item_type=SandboxWikibase().WIKIPEDIA_REFERENCE
    #     )
    #     assert len(ref_items) == 1

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_uploading_a_page_reference_and_website_item_twice(self):
        # wcd = WikibaseCrudDelete(wikibase=SandboxWikibase())
        # wcd.delete_imported_items()
        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Democracy"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        # This reference is the first one on https://en.wikipedia.org/w/index.php?title=Democracy&action=edit
        reference = EnglishWikipediaPageReference(
            **{
                "agency": "Oxford University Press",
                "access-date": "24 February 2021",
                "title": "Democracy",
                "template_name": "cite news",
                "url": "https://www.oxfordreference.com/view/10.1093/acref/9780195148909.001.0001/acref-9780195148909-e-241",
            }
        )
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wppage.references = []
        wppage.references.append(reference)
        wppage.references.append(reference)
        wppage.__upload_references_and_websites_if_missing__()
        # We have no assertions in this test.
        # It is successful if no exceptions other than
        # NonUniqueLabelDescriptionPairError are raised.

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_publisher_and_location_statements(self):
        data = dict(
            template_name="cite web",
            url="http://www.kmk.a.se/ImageUpload/kmkNytt0110.pdf",
            archive_url="https://web.archive.org/web/20100812051822/http://www.kmk.a.se/ImageUpload/kmkNytt0110.pdf",
            url_status="dead",
            archive_date="2010-08-12",
            title="Musköbasen 40 år",
            first="Helene",
            last="Skoglund",
            author2="Nynäshamns Posten",
            date="January 2010",
            publisher="Kungliga Motorbåt Klubben",
            location="Stockholm",
            pages="4–7",
            language="Swedish",
            trans_title="Muskö Naval Base 40 years",
            access_date="2010-11-09",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        assert item.claims.get(property=wc.wikibase.PUBLISHER_STRING) is not None
        assert item.claims.get(property=wc.wikibase.LOCATION_STRING) is not None
        claim: List[Claim] = item.claims.get(property=wc.wikibase.ARCHIVE_URL)
        assert claim[0] is not None
        # print(claim[0].qualifiers)
        assert claim[0].qualifiers is not None

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_internet_archive_id_statement(self):
        data = dict(
            url="https://archive.org/details/catalogueofshipw0000wils/",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        assert item.claims.get(property=wc.wikibase.INTERNET_ARCHIVE_ID) is not None

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_google_books_id_statement(self):
        data = dict(
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        assert item.claims.get(property=wc.wikibase.GOOGLE_BOOKS_ID) is not None

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_periodical_string_statement(self):
        data = dict(
            periodical="test",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        assert item.claims.get(property=wc.wikibase.PERIODICAL_STRING) is not None

    @pytest.mark.xfail(bool(getenv("CI")), reason="GitHub Actions do not have logins")
    def test_oclc_statement(self):
        data = dict(
            oclc="test",
            url="https://books.google.ca/books?id=on0TaPqFXbcC&pg=PA431",
            template_name="cite book",
        )
        reference = EnglishWikipediaPageReference(**data)
        reference.wikibase = SandboxWikibase()
        reference.finish_parsing_and_generate_hash()
        wc = WikibaseCrudCreate(wikibase=SandboxWikibase())
        from src.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage

        wppage = WikipediaPage(wikibase=SandboxWikibase())
        title = "Test"
        wppage.__get_wikipedia_page_from_title__(title=title)
        wppage.__generate_hash__()
        item = wc.__prepare_new_reference_item__(
            page_reference=reference, wikipedia_page=wppage
        )
        assert item.claims.get(property=wc.wikibase.OCLC_CONTROL_NUMBER) is not None
