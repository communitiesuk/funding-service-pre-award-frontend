from collections import OrderedDict

import pytest

from assess.assessments.models.location_data import LocationData

# Given data
input_data_list = [
    {
        "local_authority": "White Horse",
        "location_json_blob": {"country": "Wales", "region": "South Wales"},
    },
    {
        "local_authority": None,
        "location_json_blob": {"country": "Scotland", "region": "Ayrshire"},
    },
]


@pytest.mark.parametrize("input_data", [input_data_list])
def test_location_data(app, input_data):
    location_data = LocationData.from_json_blob(input_data)
    assert location_data.countries == OrderedDict([("ALL", "All"), ("Scotland", "Scotland"), ("Wales", "Wales")])
    assert location_data.regions == OrderedDict(
        [
            ("ALL", "All"),
            ("Ayrshire", "Ayrshire"),
            ("South Wales", "South Wales"),
        ]
    )
    assert location_data._local_authorities == OrderedDict([("ALL", "All"), ("White Horse", "White Horse")])
