import time

from assess.services.data_services import get_fund
from assess.shared.helpers import get_ttl_hash


def test_get_fund_lru_cache(mocker):
    fund_args = {
        "name": "Testing Fund",
        "short_name": "",
        "description": "",
        "welsh_available": True,
        "title": "Test Fund by ID",
        "id": "222",
    }
    mocker.patch(
        "assess.services.data_services.get_data",
        return_value=fund_args,
    )
    # `get_fund`'s output is cached for 2 sec's
    fund = get_fund(fid="222", ttl_hash=get_ttl_hash(seconds=2))
    assert fund.id == fund_args["id"]
    assert fund.name == "Testing Fund"

    # Now let's make another call to `get_fund` with modified fund data(in db) in less than 2 sec
    fund_args["name"] = "Testing Fund 2"
    mocker.patch(
        "assess.services.data_services.get_data",
        return_value=fund_args,
    )
    fund = get_fund(fid="222", ttl_hash=get_ttl_hash(seconds=2))
    assert fund.name == "Testing Fund"  # observe that fund name is still equal to cached title

    # Sleep for 2 seconds to reset the cache & make a fresh call to `get_fund`
    time.sleep(2)
    fund = get_fund(fid="222", ttl_hash=get_ttl_hash(seconds=2))
    assert fund.name == "Testing Fund 2"
