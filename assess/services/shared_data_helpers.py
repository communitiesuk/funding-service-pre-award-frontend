from assess.services.data_services import get_assessor_task_list_state, get_fund, get_round
from assess.services.models.assessor_task_list import AssessorTaskList
from assess.shared.helpers import get_ttl_hash
from config import Config


def get_state_for_tasklist_banner(application_id) -> AssessorTaskList:
    assessor_task_list_metadata = get_assessor_task_list_state(application_id)
    fund = get_fund(
        assessor_task_list_metadata["fund_id"],
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    round = get_round(
        assessor_task_list_metadata["fund_id"],
        assessor_task_list_metadata["round_id"],
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    assessor_task_list_metadata["fund_name"] = fund.name
    assessor_task_list_metadata["fund_short_name"] = fund.short_name
    assessor_task_list_metadata["round_short_name"] = round.short_name
    assessor_task_list_metadata["fund_guidance_url"] = round.guidance_url
    assessor_task_list_metadata["is_eoi_round"] = round.is_expression_of_interest

    state = AssessorTaskList.from_json(assessor_task_list_metadata)
    return state
