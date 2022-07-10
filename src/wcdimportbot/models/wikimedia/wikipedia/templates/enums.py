from enum import Enum, auto


class WikipediaTemplatePersonRole(Enum):
    pass


class EnglishWikipediaTemplatePersonRole(WikipediaTemplatePersonRole):
    AUTHOR = "author"
    EDITOR = "editor"
    HOST = "host"
    INTERVIEWER = "interviewer"
    TRANSLATOR = "translator"
    UNKNOWN = auto()
