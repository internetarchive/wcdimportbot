from typing import Optional

from wikibaseintegrator.entities import ItemEntity  # type: ignore

from src.wcd_base_model import WcdBaseModel


class WikibaseReturn(WcdBaseModel):
    item: Optional[ItemEntity]
    item_qid: str
    uploaded_now: bool

    class Config:
        arbitrary_types_allowed = True
