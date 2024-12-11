from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

from ..models.question import Question


@dataclass
class Application:
    identifier: str
    submitted: datetime
    fund_name: str
    fund_id: str
    round_id: str
    questions: List[Question] = None
    status: str = "NOT_STARTED"
    assessment_deadline: datetime = datetime.now()

    @staticmethod
    def from_json(data: dict):
        date_submitted = data.get("date_submitted")
        if date_submitted and date_submitted != "null":
            submitted = datetime.fromisoformat(data.get("date_submitted", "1970-01-01"))
        else:
            submitted = None
        application = Application(
            identifier=data.get("id"),
            submitted=submitted,
            fund_name=data.get("fund_name"),
            fund_id=data.get("fund_id"),
            round_id=data.get("round_id"),
            status=data.get("status"),
            assessment_deadline=datetime.fromisoformat(data.get("assessment_deadline", "1970-01-01")),
        )
        if "questions" in data:
            for question_data in data["questions"]:
                question = Question.from_json(question_data)
                application.add_question(question)

        return application

    @property
    def status_display(self):
        return self.status.replace("_", " ")

    def questions_count_by_status(self, status) -> int:
        return sum(question.status == status for question in self.questions)

    @property
    def question_status_summary(self) -> dict:
        statuses = ["COMPLETED", "NOT STARTED", "IN PROGRESS"]
        summary = {}
        for status in statuses:
            summary.update({status: self.questions_count_by_status(status)})
        return summary

    def add_question(self, question: Question):
        if not self.questions:
            self.questions = []
        self.questions.append(question)

    def get_question(self, index: int) -> Union[Question, None]:
        if self.questions:
            return self.questions[index]
        return None
