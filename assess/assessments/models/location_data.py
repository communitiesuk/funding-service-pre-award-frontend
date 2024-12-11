from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class LocationData:
    """
    A class to represent location data.

    Attributes:
        locations: A list of location dictionaries.
        local_authorities: A list of local authority names.
    """

    locations: list[dict]
    local_authorities: list[str]

    @classmethod
    def from_json_blob(cls, json_blob):
        locations = [location["location_json_blob"] for location in json_blob if location is not None]
        local_authorities = [item["local_authority"] for item in json_blob if item is not None]
        return cls(locations, local_authorities)

    def _create_ordered_dict(self, key):
        """
        Creates a sorted and ordered dictionary of location data for the specified key.
        Returns an ordered dictionary of location data.
        """

        def _item(item):
            return item if key == "local_authority" else item[key]

        def _data(key):
            return self.local_authorities if key == "local_authority" else self.locations

        sorted_items = sorted([(_item(item), _item(item)) for item in _data(key) if item is not None])

        return OrderedDict({"ALL": "All", **dict(sorted_items)})

    @property
    def countries(self):
        return self._create_ordered_dict("country")

    @property
    def regions(self):
        return self._create_ordered_dict("region")

    @property
    def _local_authorities(self):
        return self._create_ordered_dict("local_authority")
