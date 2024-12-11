import inspect
from dataclasses import dataclass


@dataclass
class Banner:
    short_id: str
    project_name: str
    funding_amount_requested: int
    workflow_status: str
    fund_id: str

    @classmethod
    def from_filtered_dict(cls, d: dict):
        # Filter unknown fields from JSON dictionary
        return cls(**{k: v for k, v in d.items() if k in inspect.signature(cls).parameters})
