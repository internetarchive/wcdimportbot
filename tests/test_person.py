from unittest import TestCase

from wcdimportbot.models.person import Person
from wcdimportbot.models.wikimedia.wikipedia.templates.enums import (
    EnglishWikipediaTemplatePersonRole,
    WikipediaTemplatePersonRole,
)


class TestPerson(TestCase):
    def test_full_name(self):
        p = Person(given="test", surname="test")
        assert p.full_name == "test test"
        p2 = Person(name_string="testtest")
        assert p2.full_name == "testtest"
        p3 = Person(name_string="")
        assert p3.full_name == ""
        p4 = Person(name_string=" ", given=" ", surname=" ")
        assert p4.full_name == ""
        p5 = Person(name_string="\t", given="\t", surname="\t")
        assert p5.full_name == ""
        p6 = Person(name_string="\n", given="\n", surname="\n")
        assert p6.full_name == ""

    def test_has_number(self):
        p = Person(given="test", surname="test")
        assert p.has_number is False
        p = Person(given="test", surname="test", number_in_sequence=1)
        assert p.has_number is True

    def test_role(self):
        p = Person(
            given="test",
            surname="test",
            role=EnglishWikipediaTemplatePersonRole.TRANSLATOR,
        )
        assert isinstance(p.role, WikipediaTemplatePersonRole)

    def test_url(self):
        p = Person(given="test", surname="test", link="test")
        assert p.url == ""
        p = Person(given="test", surname="test", link="https://en.wikipedia.org/")
        assert p.url == "https://en.wikipedia.org/"
