from dataclasses import dataclass, field
from typing import List

from assess.services.models.round import Round
from assess.config.display_value_mappings import ALL_VALUE


@dataclass
class Fund:
    name: str
    id: str
    description: str
    short_name: str
    owner_organisation_name: str = ""
    owner_organisation_shortname: str = ""
    owner_organisation_logo_uri: str = ""
    funding_type: str = ""
    rounds: List[Round] = field(default_factory=list)

    @staticmethod
    def from_json(data: dict):
        return Fund(
            name=decorate_fund_name(data),
            funding_type=data.get("funding_type"),
            id=data.get("id"),
            description=data.get("description"),
            short_name=data.get("short_name"),
            owner_organisation_name=data.get("owner_organisation_name"),
            owner_organisation_shortname=data.get("owner_organisation_shortname"),
            owner_organisation_logo_uri=data.get("owner_organisation_logo_uri"),
        )

    # TODO: Move fund_type to a property on fund_store
    @property
    def fund_types(self) -> set[str]:
        return {ALL_VALUE, "competitive"}

    def add_round(self, fund_round: Round):
        if not self.rounds:
            self.rounds = []
        self.rounds.append(fund_round)


def decorate_fund_name(data: dict):
    return data.get("name") + (" - Expression of interest" if data.get("funding_type") == "EOI" else "")
