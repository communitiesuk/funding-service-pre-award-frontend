import inspect
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Score:
    id: str
    application_id: str
    sub_criteria_id: str
    score: str
    justification: str
    date_created: str
    user_id: str
    user_full_name: str
    user_email: str
    highest_role: str

    def __post_init__(self):
        self.date_created = datetime.fromisoformat(self.date_created).strftime("%Y-%m-%d %X")

    @classmethod
    def from_dict(cls, d: dict):
        # Filter unknown fields from JSON dictionary
        return cls(**{k: v for k, v in d.items() if k in inspect.signature(cls).parameters})
