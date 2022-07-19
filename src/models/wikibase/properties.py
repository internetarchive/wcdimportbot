from typing import List

from src import WcdBaseModel
from src.models.wikibase import dictionaries


class Properties(WcdBaseModel):
    """This has all the logic needed for handling our properties"""

    properties = {
        **dictionaries.wcd_externalid_properties,
        **dictionaries.wcd_item_properties,
        **dictionaries.wcd_quantity_properties,
        **dictionaries.wcd_string_properties,
        **dictionaries.wcd_time_properties,
        **dictionaries.wcd_url_properties,
    }

    def get_all_property_names(self) -> List[str]:
        """Get all labels of properties formatted with underscore and uppercase"""
        return [str(property) for property in self.properties]

    def get_all_property_labels(self) -> List[str]:
        """Get all labels of properties formatted with space and titlecase"""
        return [str(property.replace("_", " ").title()) for property in self.properties]
