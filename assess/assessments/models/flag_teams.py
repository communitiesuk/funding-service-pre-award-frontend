from dataclasses import dataclass
from typing import List

from num2words import num2words

from assess.services.models.flag import Flag, FlagType

# TODO : Check if there is better way to do it?


@dataclass
class TeamFlagStats:
    team_name: str
    num_of_flags: int
    num_of_resolved: int
    num_of_raised: int
    num_of_stopped: int
    ordinal_list: list
    flags_list: List[Flag]


@dataclass
class TeamsFlagData:
    teams_stats: dict

    @classmethod
    def from_flags(cls, flags_list: List[Flag], teams_list: list = None):
        teams_stats = {}

        if isinstance(flags_list, Flag):
            flags_list = [flags_list]

        if not teams_list:
            teams_list = [flag.latest_allocation for flag in flags_list]
            teams_list = list(set(teams_list) - set([None]))  # filter for unique teams

        for team in teams_list:
            team_flags = [f for f in flags_list if f.latest_allocation == team]
            num_of_flags = len(team_flags)
            num_of_raised = len([f for f in team_flags if f.latest_status == FlagType.RAISED])
            num_of_resolved = len([f for f in team_flags if f.latest_status == FlagType.RESOLVED])
            num_of_stopped = len([f for f in team_flags if f.latest_status == FlagType.STOPPED])

            ordinal_list = [num2words(index, to="ordinal").capitalize() for index, _ in enumerate(team_flags, start=1)]

            teams_stats[team] = TeamFlagStats(
                team_name=team,
                num_of_flags=num_of_flags,
                num_of_resolved=num_of_resolved,
                num_of_raised=num_of_raised,
                num_of_stopped=num_of_stopped,
                ordinal_list=list(reversed(ordinal_list)),
                flags_list=list(reversed(team_flags)),
            )

        return cls(teams_stats=teams_stats)
