from marshmallow import post_load

from wcdimportbot.models.wikimedia.wikipedia.templates.wikipedia_page_reference import (
    WikipediaPageReference,
    WikipediaPageReferenceSchema,
)


class EnglishWikipediaPageReference(WikipediaPageReference):
    pass


class EnglishWikipediaPageReferenceSchema(WikipediaPageReferenceSchema):
    @post_load
    # **kwargs is needed here despite what the validator claims
    def return_object(self, data, **kwargs):  # type: ignore
        return EnglishWikipediaPageReference(**data)
