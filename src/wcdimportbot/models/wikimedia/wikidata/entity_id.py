# import logging
# from typing import Optional
#
# from pydantic.dataclasses import dataclass
# from wikibaseintegrator import wbi_config   # type: ignore
#
# import config
# from wcdimportbot.models.wikimedia.enums import WikidataNamespaceLetters
#
# wbi_config.config['USER_AGENT'] = config.user_agent
#
#
# @dataclass
# class EntityId:
#     raw_identifier: str
#     letter: Optional[WikidataNamespaceLetters] = None
#     rest: Optional[str] = None
#
#     @property
#     def value(self):
#         return f"{self.letter.value}{self.rest}"
#
#     # See https://pydantic-docs.helpmanual.io/usage/dataclasses/
#     def __post_init_post_parse__(self):
#         logger = logging.getLogger(__name__)
#         if self.raw_identifier is not None:
#             # Remove prefix if found
#             logger.debug("Removing prefixes")
#             for prefix in config.wikidata_prefixes:
#                 if prefix in self.raw_identifier:
#                     self.raw_identifier = self.raw_identifier.replace(prefix, "")
#             if len(self.raw_identifier) > 1:
#                 logger.debug(f"entity_id:{self.raw_identifier}")
#                 self.letter = WikidataNamespaceLetters(self.raw_identifier[0:1])
#                 self.rest = self.raw_identifier[1:]
#             else:
#                 raise ValueError("Entity ID was too short.")
#         else:
#             raise ValueError("Entity ID was None")
#
#     def __str__(self):
#         return f"{self.letter.value}{self.rest}"
#
#     def history_url(self):
#         return f"https://www.wikidata.org/w/index.php?title={self.value}&action=history"
#
#     def url(self):
#         return f"{config.wikidata_entity_prefix}{str(self)}"
#
#     # def extract_wdqs_json_entity_id(self, json: Dict, sparql_variable: str):
#     #     self.__init__(json[sparql_variable]["value"].replace(
#     #         config.wikidata_entity_prefix, ""
#     #     ))
