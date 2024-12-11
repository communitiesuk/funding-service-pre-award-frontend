from dataclasses import dataclass


@dataclass
class QuestionField:
    key: str
    title: str
    field_type: str
    answer: str

    @staticmethod
    def from_json(data: dict):
        return QuestionField(
            key=data.get("key"),
            title=data.get("title"),
            field_type=data.get("field_type"),
            answer=data.get("answer"),
        )
