import enum
import inspect
from dataclasses import dataclass

from assess.services.models.theme import Theme


@dataclass()
class SubCriteria:
    id: str
    name: str
    themes: list[Theme]
    funding_amount_requested: int
    project_name: str
    fund_id: str
    workflow_status: str
    short_id: str
    is_scored: bool

    def __post_init__(self):
        self.themes = [Theme.from_filtered_dict(theme) for theme in self.themes]
        if isinstance(self.workflow_status, enum.Enum):
            self.workflow_status = self.workflow_status.name

    @classmethod
    def from_filtered_dict(cls, d: dict):
        # Filter unknown fields from JSON dictionary
        return cls(**{k: v for k, v in d.items() if k in inspect.signature(cls).parameters})
