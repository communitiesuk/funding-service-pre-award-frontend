import ast
from dataclasses import dataclass
from typing import List

from .question_field import QuestionField


@dataclass
class Question:
    title: str
    status: str
    fields: List[QuestionField] = None

    @staticmethod
    def from_json(data: dict):
        question = Question(title=data.get("question"), status=data.get("status"))
        if "fields" in data:
            for field_data in data["fields"]:
                field = QuestionField.from_json(field_data)
                question.add_field(field)

        return question

    def add_field(self, field: QuestionField):
        if not self.fields:
            self.fields = []
        self.fields.append(field)

    def as_structured_question(self):
        answers_per_question_field = {}
        for question_field in self.fields:
            answer = question_field.answer
            try:
                if type(ast.literal_eval(answer)) is list:
                    answers_per_question_field[question_field.title] = ast.literal_eval(answer)
                    continue
            except (ValueError, SyntaxError):
                # literal_eval cannot parse string values
                pass
            answers_per_question_field[question_field.title] = [answer]

        return answers_per_question_field
