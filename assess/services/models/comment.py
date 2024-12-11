import inspect
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class CommentType(Enum):
    COMMENT = auto()

    WHOLE_APPLICATION = auto()


@dataclass
class Comment:
    id: str
    user_id: str
    date_created: str
    email_address: str
    full_name: str
    highest_role: str
    theme_id: str
    fund_short_name: str
    updates: list
    application_id: str
    sub_criteria_id: str
    comment_type: CommentType

    def __post_init__(self):
        for item in self.updates:
            item["date_created"] = datetime.fromisoformat(item["date_created"]).strftime("%Y-%m-%d %X")

        # sort the updates in the order they are created
        if self.updates:
            self.updates = sorted(self.updates, key=lambda x: x["date_created"])

    @classmethod
    def from_dict(cls, d: dict):
        # Filter unknown fields from JSON dictionary
        return cls(**{k: v for k, v in d.items() if k in inspect.signature(cls).parameters})

    @property
    def from_lead_assessor(self):
        return f"{self.fund_short_name}_{self.highest_role}" == f"{self.fund_short_name}_LEAD_ASSESSOR"

    @property
    def from_assessor(self):
        return f"{self.fund_short_name}_{self.highest_role}" == f"{self.fund_short_name}_ASSESSOR"

    @property
    def from_any_assessor(self):
        return self.from_lead_assessor or self.from_assessor
