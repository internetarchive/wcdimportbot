from unittest import TestCase

from src import SandboxWikibase, console
from wcdimportbot.helpers.template_extraction import extract_templates_and_params
from wcdimportbot.models.wikimedia.wikipedia.templates.google_books import (
    GoogleBooks,
    GoogleBooksSchema,
)


class TestGoogleBooks(TestCase):
    def test_parsing_into_object(self):
        data = "{{google books |plainurl=y |id=CDJpAAAAMAAJ |page=313}}"
        template_tuples = extract_templates_and_params(data, True)
        for _template_name, content in template_tuples:
            gb: GoogleBooks = GoogleBooksSchema().load(content)
            gb.wikibase = SandboxWikibase()
            gb.finish_parsing()
            console.print(gb.dict())
            assert gb.url == "https://books.google.com/books?id=CDJpAAAAMAAJ"
