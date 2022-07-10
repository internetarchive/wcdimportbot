# from typing import Optional, List
#
# from pydantic import BaseModel
# from wikibaseintegrator import wbi_config, WikibaseIntegrator  # type: ignore
# from wikibaseintegrator.entities import Item as EntityItem  # type: ignore
#
# import config
# from wcdimportbot.models.wikimedia.enums import WikimediaLanguage
# from wcdimportbot.models.wikimedia.wikidata.entity_id import EntityId
#
#
# class Item(WcdBaseModel):
#     qid: Optional[EntityId]
#     __item: Optional[EntityItem]
#     __aliases: Optional[List[str]]
#     __description: Optional[str]
#
#     @property
#     def aliases(self):
#         if self.__item is None:
#             self.__fetch__()
#         if self.__aliases is None:
#             self.__aliases = self.__item.aliases.get(WikimediaLanguage.ENGLISH.value)
#         return self.__aliases
#
#     @property
#     def description(self):
#         if self.__item is None:
#             self.__fetch__()
#         if self.__description is None:
#             self.__description = self.__item.descriptions.get(WikimediaLanguage.ENGLISH.value)
#         return self.__description
#
#     def __fetch__(self):
#         # fetch using WBI
#         wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
#         wbi = WikibaseIntegrator(login=None)
#         self.__item = wbi.item.get()
#
#     # @staticmethod
#     # def __call_wbi_search_entities__(subject):
#     #     return search_entities(search_string=subject,
#     #                            language="en",
#     #                            dict_result=True,
#     #                            max_results=1)
#
